from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from ..database import get_session
from ..models import Appointment, AppointmentStatus, ConsultationNote, User, DoctorProfile, Role
from ..services.llm import generate_pre_visit_summary, generate_post_visit_summary
from ..services.notifications import send_booking_email, create_calendar_event

router = APIRouter()

class HoldSlotRequest(BaseModel):
    doctor_id: int
    patient_id: int
    start_time: datetime
    end_time: datetime

class ConfirmAppointmentRequest(BaseModel):
    appointment_id: int
    symptoms: str

class PostVisitRequest(BaseModel):
    notes: str
    prescription: Optional[str] = None

@router.post("/hold")
def hold_slot(req: HoldSlotRequest, session: Session = Depends(get_session)):
    # Check for existing confirmed or active holds for this doctor at this time
    now = datetime.now()
    
    # We use a transaction (or at least check) to prevent double booking.
    # In a real high-concurrency app, we'd use SELECT FOR UPDATE or a unique constraint.
    existing = session.exec(
        select(Appointment).where(
            Appointment.doctor_id == req.doctor_id,
            Appointment.start_time == req.start_time,
            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.HOLD])
        )
    ).all()
    
    for appt in existing:
        if appt.status == AppointmentStatus.CONFIRMED:
            raise HTTPException(status_code=409, detail="Slot already booked")
        if appt.status == AppointmentStatus.HOLD and appt.hold_expires_at > now:
            raise HTTPException(status_code=409, detail="Slot is currently held by someone else")

    # Create hold
    hold_expires = now + timedelta(minutes=5)
    new_appt = Appointment(
        patient_id=req.patient_id,
        doctor_id=req.doctor_id,
        start_time=req.start_time,
        end_time=req.end_time,
        status=AppointmentStatus.HOLD,
        hold_expires_at=hold_expires
    )
    session.add(new_appt)
    session.commit()
    session.refresh(new_appt)
    
    return {"message": "Slot held for 5 minutes", "appointment_id": new_appt.id, "expires_at": hold_expires}

@router.post("/confirm")
def confirm_appointment(req: ConfirmAppointmentRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    appt = session.get(Appointment, req.appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    if appt.status != AppointmentStatus.HOLD:
        raise HTTPException(status_code=400, detail="Appointment is not in HOLD status")
        
    if appt.hold_expires_at and appt.hold_expires_at < datetime.now():
        raise HTTPException(status_code=400, detail="Hold has expired")
        
    # Generate Pre-visit summary via LLM
    llm_result = generate_pre_visit_summary(req.symptoms)
    
    consultation = ConsultationNote(
        appointment_id=appt.id,
        symptoms=req.symptoms,
        pre_visit_summary=llm_result["full_summary"],
        urgency_level=llm_result["urgency_level"],
        suggested_questions=llm_result["suggested_questions"]
    )
    session.add(consultation)
    
    appt.status = AppointmentStatus.CONFIRMED
    session.add(appt)
    session.commit()
    
    # In background, send emails and calendar
    patient = session.get(User, appt.patient_id)
    doctor = session.get(User, appt.doctor_id)
    
    background_tasks.add_task(send_booking_email, patient.email, doctor.email, appt.start_time, appt.end_time)
    background_tasks.add_task(create_calendar_event, patient.email, doctor.email, appt.start_time, appt.end_time)
    
    return {"message": "Appointment confirmed", "appointment_id": appt.id}

@router.post("/{appointment_id}/post-visit")
def submit_post_visit(appointment_id: int, req: PostVisitRequest, session: Session = Depends(get_session)):
    appt = session.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    consultation = session.exec(select(ConsultationNote).where(ConsultationNote.appointment_id == appointment_id)).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation note not found")
        
    # Generate post-visit summary via LLM
    patient_friendly_summary = generate_post_visit_summary(req.notes)
    
    consultation.post_visit_notes = req.notes
    consultation.prescription = req.prescription
    consultation.post_visit_summary = patient_friendly_summary
    
    appt.status = AppointmentStatus.COMPLETED
    session.add(consultation)
    session.add(appt)
    session.commit()
    
    return {"message": "Post-visit notes saved", "patient_friendly_summary": patient_friendly_summary}
