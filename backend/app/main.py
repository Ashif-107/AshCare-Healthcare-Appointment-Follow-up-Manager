from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import create_db_and_tables
from .routers import auth, doctors, appointments, leaves, admin

app = FastAPI(title="Healthcare Appointment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
app.include_router(leaves.router, prefix="/admin/leaves", tags=["Admin Leaves"])
app.include_router(admin.router, prefix="/admin", tags=["Admin System"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Healthcare Appointment API"}
