def send_booking_email(patient_email: str, doctor_email: str, start_time, end_time):
    print(f"[MOCK EMAIL] Booking confirmed for {patient_email} with doctor {doctor_email} at {start_time}")
    
def send_cancellation_email(patient_email: str, doctor_email: str, start_time):
    print(f"[MOCK EMAIL] Booking CANCELLED for {patient_email} with doctor {doctor_email} at {start_time}")

def create_calendar_event(patient_email: str, doctor_email: str, start_time, end_time):
    print(f"[MOCK CALENDAR] Event created for {patient_email} and {doctor_email} from {start_time} to {end_time}")
    
def delete_calendar_event(event_id: str):
    print(f"[MOCK CALENDAR] Event {event_id} deleted")
