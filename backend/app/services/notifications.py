import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Google Calendar Imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SCOPES = ['https://www.googleapis.com/auth/calendar']

def _get_calendar_service():
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), '..', '..', 'token.json')
    credentials_path = os.path.join(os.path.dirname(__file__), '..', '..', 'credentials.json')
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                pass
        
        if not creds or not creds.valid:
            if not os.path.exists(credentials_path):
                print("[Google Calendar] Error: credentials.json not found in backend directory.")
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"[Google Calendar] Error authenticating: {e}")
                return None
                
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"[Google Calendar] Error building service: {e}")
        return None

def send_email(to_email: str, subject: str, html_body: str):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print(f"[MOCK EMAIL] Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD in .env. Would send to {to_email}: {subject}")
        return
        
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[Email Server] Successfully sent email to {to_email}")
    except Exception as e:
        print(f"[Email Server] Failed to send email to {to_email}: {e}")

def send_booking_email(patient_email: str, doctor_email: str, start_time: datetime, end_time: datetime):
    print(f"Triggering email for {patient_email} and {doctor_email}")
    subject = "Appointment Confirmation - AshCare"
    
    body = f"""
    <h2>Appointment Confirmed</h2>
    <p>Your appointment has been successfully scheduled.</p>
    <p><strong>Date & Time:</strong> {start_time.strftime('%B %d, %Y at %I:%M %p')}</p>
    <p>Thank you for choosing AshCare!</p>
    """
    
    send_email(patient_email, subject, body)
    send_email(doctor_email, "New Appointment Scheduled", body)

def send_cancellation_email(patient_email: str, doctor_email: str, start_time: datetime):
    subject = "Appointment Cancellation - AshCare"
    
    body = f"""
    <h2>Appointment Cancelled</h2>
    <p>Your appointment scheduled for {start_time.strftime('%B %d, %Y at %I:%M %p')} has been cancelled.</p>
    <p>If you have any questions, please contact the admin.</p>
    """
    
    send_email(patient_email, subject, body)
    send_email(doctor_email, "Appointment Cancelled", body)

def create_calendar_event(patient_email: str, doctor_email: str, start_time: datetime, end_time: datetime):
    service = _get_calendar_service()
    if not service:
        print(f"[MOCK CALENDAR] Would create event for {patient_email} and {doctor_email}")
        return
        
    event = {
      'summary': 'AshCare Medical Appointment',
      'description': 'Consultation between patient and doctor.',
      'start': {
        'dateTime': start_time.isoformat(),
        'timeZone': 'UTC',
      },
      'end': {
        'dateTime': end_time.isoformat(),
        'timeZone': 'UTC',
      },
      'attendees': [
        {'email': patient_email},
        {'email': doctor_email},
      ],
      'reminders': {
        'useDefault': True,
      },
      'conferenceData': {
        'createRequest': {
            'requestId': f"{patient_email}-{start_time.timestamp()}",
            'conferenceSolutionKey': {'type': 'hangoutsMeet'}
        }
      }
    }

    try:
        event = service.events().insert(
            calendarId='primary', 
            body=event,
            conferenceDataVersion=1
        ).execute()
        print(f"[Google Calendar] Event created: {event.get('htmlLink')}")
        return event.get('id')
    except Exception as e:
        print(f"[Google Calendar] Error creating event: {e}")
        return None

def delete_calendar_event(event_id: str):
    service = _get_calendar_service()
    if not service:
        print(f"[MOCK CALENDAR] Would delete event {event_id}")
        return
        
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        print(f"[Google Calendar] Event {event_id} deleted successfully.")
    except Exception as e:
        print(f"[Google Calendar] Error deleting event {event_id}: {e}")
