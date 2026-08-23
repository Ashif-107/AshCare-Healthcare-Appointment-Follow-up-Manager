import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.notifications import (
    send_booking_email,
    send_cancellation_email,
    create_calendar_event,
    delete_calendar_event
)

def test_all():
    print("=== Testing AshCare Integrations ===")
    load_dotenv()
    
    # 1. Check Env
    gmail = os.getenv("GMAIL_ADDRESS")
    pwd = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail or not pwd:
        print("WARNING: GMAIL_ADDRESS or GMAIL_APP_PASSWORD is not set in .env")
        print("Emails will NOT be sent.")
    else:
        print(f"Email configured for: {gmail}")
        
    creds_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
    if not os.path.exists(creds_path):
        print("WARNING: credentials.json not found in the backend directory.")
        print("Google Calendar events will NOT be created.")
    else:
        print("credentials.json found. Calendar integration is ready.")
        
    patient_email = input("\nEnter a patient email to test with: ")
    doctor_email = input("Enter a doctor email to test with: ")
    
    start_time = datetime.utcnow() + timedelta(days=1)
    end_time = start_time + timedelta(minutes=30)
    
    print("\n--- Testing Email ---")
    print("Sending Booking Email...")
    send_booking_email(patient_email, doctor_email, start_time, end_time)
    
    print("Sending Cancellation Email...")
    send_cancellation_email(patient_email, doctor_email, start_time)
    
    print("\n--- Testing Calendar ---")
    print("Attempting to create a calendar event...")
    event_id = create_calendar_event(patient_email, doctor_email, start_time, end_time)
    
    if event_id:
        print(f"Success! Event ID: {event_id}")
        delete = input("Do you want to test deleting this event? (y/n): ")
        if delete.lower() == 'y':
            delete_calendar_event(event_id)
    else:
        print("Calendar event creation skipped or failed.")
        
    print("\nTest completed.")

if __name__ == "__main__":
    test_all()
