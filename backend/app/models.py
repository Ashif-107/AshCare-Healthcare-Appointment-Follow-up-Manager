from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum

class Role(str, Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"

class AppointmentStatus(str, Enum):
    HOLD = "HOLD"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    CANCELLED_DUE_TO_LEAVE = "CANCELLED_DUE_TO_LEAVE"
    COMPLETED = "COMPLETED"

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: str
    role: Role

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    
    doctor_profile: Optional["DoctorProfile"] = Relationship(back_populates="user")
    patient_appointments: List["Appointment"] = Relationship(back_populates="patient", sa_relationship_kwargs={"foreign_keys": "[Appointment.patient_id]"})
    doctor_appointments: List["Appointment"] = Relationship(back_populates="doctor", sa_relationship_kwargs={"foreign_keys": "[Appointment.doctor_id]"})

class DoctorProfileBase(SQLModel):
    specialization: str
    working_hours_start: time
    working_hours_end: time
    slot_duration_minutes: int = Field(default=30)

class DoctorProfile(DoctorProfileBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    
    user: User = Relationship(back_populates="doctor_profile")
    leaves: List["Leave"] = Relationship(back_populates="doctor")

class Leave(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="doctorprofile.id")
    leave_date: date
    reason: Optional[str] = None
    
    doctor: DoctorProfile = Relationship(back_populates="leaves")

class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="user.id")
    doctor_id: int = Field(foreign_key="user.id")
    start_time: datetime = Field(index=True)
    end_time: datetime
    status: AppointmentStatus = Field(default=AppointmentStatus.HOLD)
    hold_expires_at: Optional[datetime] = None
    
    patient: User = Relationship(back_populates="patient_appointments", sa_relationship_kwargs={"foreign_keys": "[Appointment.patient_id]"})
    doctor: User = Relationship(back_populates="doctor_appointments", sa_relationship_kwargs={"foreign_keys": "[Appointment.doctor_id]"})
    
    consultation: Optional["ConsultationNote"] = Relationship(back_populates="appointment")

class ConsultationNote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    appointment_id: int = Field(foreign_key="appointment.id", unique=True)
    symptoms: str
    pre_visit_summary: Optional[str] = None
    urgency_level: Optional[str] = None # Low / Medium / High
    suggested_questions: Optional[str] = None
    
    post_visit_notes: Optional[str] = None
    prescription: Optional[str] = None
    post_visit_summary: Optional[str] = None
    
    appointment: Appointment = Relationship(back_populates="consultation")
