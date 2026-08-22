from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from datetime import date, datetime
from typing import List
from pydantic import BaseModel
from ..database import get_session
from ..models import Leave, DoctorProfile, Appointment, AppointmentStatus, User
from ..services.notifications import send_cancellation_email, delete_calendar_event
from ..dependencies import get_admin_user

router = APIRouter()

class LeaveRequest(BaseModel):
    doctor_id: int
    leave_date: date
    reason: str = ""

@router.post("/")
def add_leave(
    req: LeaveRequest, 
    background_tasks: BackgroundTasks, 
    current_admin: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    doc_profile = session.exec(select(DoctorProfile).where(DoctorProfile.user_id == req.doctor_id)).first()
    if not doc_profile:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    # Check if already on leave
    existing = session.exec(select(Leave).where(Leave.doctor_id == doc_profile.id, Leave.leave_date == req.leave_date)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Doctor already on leave for this date")
        
    leave = Leave(doctor_id=doc_profile.id, leave_date=req.leave_date, reason=req.reason)
    session.add(leave)
    
    # Find existing appointments on this date and cancel them
    start_of_day = datetime.combine(req.leave_date, datetime.min.time())
    end_of_day = datetime.combine(req.leave_date, datetime.max.time())
    
    affected_appts = session.exec(
        select(Appointment).where(
            Appointment.doctor_id == req.doctor_id,
            Appointment.start_time >= start_of_day,
            Appointment.start_time <= end_of_day,
            Appointment.status == AppointmentStatus.CONFIRMED
        )
    ).all()
    
    for appt in affected_appts:
        appt.status = AppointmentStatus.CANCELLED_DUE_TO_LEAVE
        session.add(appt)
        
        # Schedule background cancellation notifications
        patient = session.get(User, appt.patient_id)
        doctor = session.get(User, appt.doctor_id)
        
        background_tasks.add_task(send_cancellation_email, patient.email, doctor.email, appt.start_time)
        # Mock delete event (we'd need event ID in a real scenario)
        background_tasks.add_task(delete_calendar_event, f"event_{appt.id}")
        
    session.commit()
    
    return {
        "message": "Leave added successfully", 
        "affected_appointments_cancelled": len(affected_appts)
    }
