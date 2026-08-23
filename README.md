# Healthcare Appointment & Follow-up Manager

A full-stack application built with Next.js (Frontend) and FastAPI (Backend) to manage healthcare appointments, AI-generated summaries, and doctor leaves.

## Documentation

- Live Code - https://ashcare.vercel.app

- [Application Screenshots](SCREENSHOTS.md)
- [DB Schema Represenation](DB_SCHEMA.md)
- [System Architecture Documentation](ARCHITECTURE.md)

## Setup Guide

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- PostgreSQL (Supabase or local)
- Groq API Key (for LLM)

### Backend Setup
1. Navigate to the `backend` directory.
2. Create a virtual environment: `python -m venv venv` and activate it.
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in the values.
5. Run the server: `uvicorn app.main:app --reload`
6. API Documentation (Swagger) is available at `http://localhost:8000/docs`

### Frontend Setup
1. Navigate to the `frontend` directory.
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`
4. Open `http://localhost:3000` in your browser.

### External APIs Setup (Email & Calendar)
To enable real email notifications and Google Calendar event creation:
1. **Gmail Setup**: Go to your Google Account > Security. Enable 2-Step Verification, and generate an "App Password".
2. **Calendar Setup**: Go to the Google Cloud Console, create a Project, and enable the **Google Calendar API**.
3. Go to Credentials, create an OAuth 2.0 Client ID (Desktop App), download the JSON file, rename it to `credentials.json`, and place it in the `backend/` directory.
4. Fill in `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` in your `backend/.env`.

## .env.example
```
DATABASE_URL=postgresql://user:password@db.supabase.co:5432/postgres
SECRET_KEY=your-jwt-secret-key
GROQ_API_KEY=your-groq-api-key
GMAIL_ADDRESS=your.email@gmail.com
GMAIL_APP_PASSWORD=your16charpassword
```
## Sample Credentials

Admin
Email: admin@ashcare.com
Password: admin123

Doctor
Email: doctor@ashcare.com
Password: doctor123
<br>
Email: paul@ashcare.com
Password: doctor456

Patient
Email: user1@gmail.com
Password: user@123

#### You can create your Own credentials and real emails for email notification and calenders 

## DB Schema (SQLModel / PostgreSQL)
- **User**: `id`, `email`, `full_name`, `hashed_password`, `role` (ADMIN, DOCTOR, PATIENT)
- **DoctorProfile**: `id`, `user_id`, `specialization`, `working_hours_start`, `working_hours_end`, `slot_duration_minutes`
- **Leave**: `id`, `doctor_id`, `leave_date`, `reason`
- **Appointment**: `id`, `patient_id`, `doctor_id`, `start_time`, `end_time`, `status` (HOLD, PENDING, CONFIRMED, CANCELLED, COMPLETED), `hold_expires_at`
- **ConsultationNote**: `id`, `appointment_id`, `symptoms`, `pre_visit_summary`, `urgency_level`, `suggested_questions`, `post_visit_notes`, `prescription`, `post_visit_summary`


---

# System Design Write-up

### Double-Booking Prevention
- **Database Transaction Checks:** During the slot hold and booking process, the system queries the `Appointment` table for any records with the same `doctor_id` and `start_time` that have a status of `CONFIRMED` or an active `HOLD`. 
- **Conflict Response:** If a conflict is found, a `409 Conflict` response is returned. 
- **Production Reinforcement:** In a high-concurrency environment, this is reinforced by applying a unique compound constraint in PostgreSQL on `(doctor_id, start_time)` filtered by active statuses, or by using pessimistic locking (`SELECT ... FOR UPDATE`) when acquiring a slot.

### Slot Hold Mechanism
- **Simultaneous Booking Handling:** To handle simultaneous booking attempts gracefully, a "Slot Hold" mechanism is implemented. 
- **Temporary Hold Creation:** When a patient selects a time slot and begins filling out their symptoms, the frontend calls the `/appointments/hold` endpoint. This creates an `Appointment` record with a `HOLD` status and a `hold_expires_at` timestamp set to 5 minutes in the future. 
- **Slot Visibility:** While this hold is active, other users querying available slots will not see this time slot. 
- **Hold Expiration:** If the patient completes the booking before expiration, the status changes to `CONFIRMED`. If they abandon the flow, the hold expires natively. 
- **Dynamic Filtering:** The slot fetching API dynamically filters out `HOLD` records where `hold_expires_at` is in the past, effectively releasing the slot without requiring an active cleanup daemon.

### Doctor Leave Conflict Handling
- **Multi-step Conflict Resolution:** When an admin or doctor marks a leave day via the `/admin/leaves` API, the system executes a resolution process within a single database transaction. 
- **Verification and Insertion:** It verifies the doctor isn't already on leave, inserts the `Leave` record, and queries all `CONFIRMED` appointments for that specific doctor on the leave date.
- **Status Updates:** The system iterates through these affected appointments, updating their status to `CANCELLED_DUE_TO_LEAVE`. 
- **Background Notifications:** To ensure patients are promptly informed, the backend uses FastAPI's `BackgroundTasks` to queue notification jobs. These jobs handle dispatching cancellation emails and invoking the Google Calendar API to delete the previously scheduled events.

### Notification Failure Handling
- **Risk Mitigation:** Relying on external services introduces the risk of network failures or API rate limits. 
- **Persistent Task Queue:** To handle this reliably, the background jobs should be upgraded to use a persistent task queue like Celery or RQ backed by Redis.
- **Retry Mechanism:** When an email or calendar API call fails, the task runner catches the exception and schedules a retry with exponential backoff. 
- **Failure Logging:** For critical failures that exceed the maximum retry count, the failure is logged into a dedicated `NotificationLog` table with a status of `FAILED`. 
- **System Monitoring:** An admin dashboard or cron job can monitor these failed logs to alert the administrator or allow manual re-triggering of notifications.

### Real Email & Google Calendar API Integrations
The application goes beyond mock notifications by directly integrating with real third-party APIs asynchronously via FastAPI's `BackgroundTasks`. 
- **Email Notifications**: Powered by Python's `smtplib` and `email.mime`, the backend establishes a secure TLS connection to `smtp.gmail.com` to dispatch HTML-formatted booking confirmations and cancellation notices to any email address.
- **Google Calendar API**: Using the `google-api-python-client` and OAuth 2.0, the backend communicates with the Google Calendar API. Upon a confirmed booking, the system creates a calendar event, provisions a live Google Meet link, and automatically invites both the doctor and the patient. If an appointment is cancelled (e.g., due to a doctor's leave), the backend dynamically queries and deletes the corresponding calendar event.
