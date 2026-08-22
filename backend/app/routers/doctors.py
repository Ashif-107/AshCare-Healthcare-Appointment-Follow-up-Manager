from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from datetime import date, datetime, timedelta
from ..database import get_session
from ..models import User, DoctorProfile, Role, Leave, Appointment, AppointmentStatus
from pydantic import BaseModel

router = APIRouter()

class DoctorInfo(BaseModel):
    id: int
    full_name: str
    specialization: str
    
class Slot(BaseModel):
    start_time: datetime
    end_time: datetime
    available: bool

@router.get("/", response_model=List[DoctorInfo])
def get_doctors(specialization: Optional[str] = None, session: Session = Depends(get_session)):
    query = select(User, DoctorProfile).join(DoctorProfile).where(User.role == Role.DOCTOR)
    if specialization:
        query = query.where(DoctorProfile.specialization.ilike(f"%{specialization}%"))
    
    results = session.exec(query).all()
    
    doctors = []
    for user, profile in results:
        doctors.append(DoctorInfo(id=user.id, full_name=user.full_name, specialization=profile.specialization))
    return doctors

@router.get("/{doctor_id}/slots", response_model=List[Slot])
def get_doctor_slots(doctor_id: int, target_date: date, session: Session = Depends(get_session)):
    doc_profile = session.exec(select(DoctorProfile).where(DoctorProfile.user_id == doctor_id)).first()
    if not doc_profile:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    # Check if doctor is on leave
    leave = session.exec(select(Leave).where(Leave.doctor_id == doc_profile.id, Leave.leave_date == target_date)).first()
    if leave:
        return [] # No slots if on leave
        
    # Fetch existing appointments for the day
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    
    appointments = session.exec(
        select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.start_time >= start_of_day,
            Appointment.start_time <= end_of_day,
            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.HOLD])
        )
    ).all()
    
    # Filter out expired holds
    now = datetime.now()
    active_appointments = []
    for appt in appointments:
        if appt.status == AppointmentStatus.HOLD and appt.hold_expires_at and appt.hold_expires_at < now:
            continue
        active_appointments.append(appt)
    
    # Generate slots based on working hours
    working_start = datetime.combine(target_date, doc_profile.working_hours_start)
    working_end = datetime.combine(target_date, doc_profile.working_hours_end)
    slot_duration = timedelta(minutes=doc_profile.slot_duration_minutes)
    
    slots = []
    current_time = working_start
    while current_time + slot_duration <= working_end:
        slot_end = current_time + slot_duration
        
        # Check availability
        is_available = True
        for appt in active_appointments:
            # Overlap check
            if (current_time < appt.end_time and slot_end > appt.start_time):
                is_available = False
                break
                
        # Also check if slot is in the past
        if current_time < now:
            is_available = False
            
        slots.append(Slot(start_time=current_time, end_time=slot_end, available=is_available))
        current_time += slot_duration
        
    return slots
