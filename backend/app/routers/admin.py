from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Annotated

from ..database import get_session
from ..models import User, Role, DoctorProfile
from ..auth import get_password_hash
from ..dependencies import get_admin_user

router = APIRouter()

class DoctorCreate(BaseModel):
    email: str
    password: str
    full_name: str
    specialization: str

@router.post("/doctors")
def create_doctor(
    doctor_data: DoctorCreate, 
    current_admin: Annotated[User, Depends(get_admin_user)],
    session: Session = Depends(get_session)
):
    db_user = session.exec(select(User).where(User.email == doctor_data.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(doctor_data.password)
    new_user = User(
        email=doctor_data.email, 
        full_name=doctor_data.full_name, 
        role=Role.DOCTOR, 
        hashed_password=hashed_password
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    from datetime import time
    doc_profile = DoctorProfile(
        user_id=new_user.id, 
        specialization=doctor_data.specialization, 
        working_hours_start=time(9,0), 
        working_hours_end=time(17,0)
    )
    session.add(doc_profile)
    session.commit()
    
    return {"message": "Doctor created successfully", "doctor_id": new_user.id}
