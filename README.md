# Healthcare Appointment & Follow-up Manager

A full-stack application built with Next.js (Frontend) and FastAPI (Backend) to manage healthcare appointments, AI-generated summaries, and doctor leaves.

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

## .env.example
```
DATABASE_URL=postgresql://user:password@db.supabase.co:5432/postgres
SECRET_KEY=your-jwt-secret-key
GROQ_API_KEY=your-groq-api-key
```
## Sample Credentials

Admin
Email: admin@ashcare.com
Password: admin123

Doctor
Email: doctor@ashcare.com
Password: doctor123
Email: paul@ashcare.com
Password: doctor456

Patient
Email: user1@gmail.com
Password: user@123

#### You cam create your Own credentials and real emails for email notification and calenders 

## DB Schema (SQLModel / PostgreSQL)
- **User**: `id`, `email`, `full_name`, `hashed_password`, `role` (ADMIN, DOCTOR, PATIENT)
- **DoctorProfile**: `id`, `user_id`, `specialization`, `working_hours_start`, `working_hours_end`, `slot_duration_minutes`
- **Leave**: `id`, `doctor_id`, `leave_date`, `reason`
- **Appointment**: `id`, `patient_id`, `doctor_id`, `start_time`, `end_time`, `status` (HOLD, PENDING, CONFIRMED, CANCELLED, COMPLETED), `hold_expires_at`
- **ConsultationNote**: `id`, `appointment_id`, `symptoms`, `pre_visit_summary`, `urgency_level`, `suggested_questions`, `post_visit_notes`, `prescription`, `post_visit_summary`



## Google Calendar Setup Steps (Conceptual)
1. Go to Google Cloud Console, create a new project.
2. Enable the Google Calendar API.
3. Set up OAuth consent screen and create OAuth 2.0 Client IDs.
4. Download the `credentials.json` file and place it in the backend root.
5. Use `google-auth-oauthlib` in Python to handle the OAuth flow and store the `token.json`.
6. Use the `google-api-python-client` to create/delete events via `service.events().insert()` or `.delete()`.

---

# System Design Write-up

### Double-Booking Prevention
Double-booking is prevented using database transaction-level checks during the slot hold and booking process. When a patient attempts to book a slot, the system queries the `Appointment` table for any records with the same `doctor_id` and `start_time` that have a status of `CONFIRMED` or an active `HOLD`. If a conflict is found, a `409 Conflict` response is returned. In a production environment with high concurrency, this is further reinforced by applying a unique compound constraint in PostgreSQL on `(doctor_id, start_time)` filtered by active statuses, or by using pessimistic locking (`SELECT ... FOR UPDATE`) when acquiring a slot.

### Slot Hold Mechanism
To handle simultaneous booking attempts gracefully, a "Slot Hold" mechanism is implemented. When a patient selects a time slot and begins filling out their symptoms, the frontend calls the `/appointments/hold` endpoint. This creates an `Appointment` record with a `HOLD` status and a `hold_expires_at` timestamp set to 5 minutes in the future. 
While this hold is active, other users querying available slots will not see this time slot. If the patient completes the booking before expiration, the status changes to `CONFIRMED`. If they abandon the flow, the hold expires natively. The slot fetching API dynamically filters out `HOLD` records where `hold_expires_at` is in the past, effectively releasing the slot without requiring an active cleanup daemon, though a background job could periodically purge expired holds to save DB space.

### Doctor Leave Conflict Handling
When an admin or doctor marks a leave day via the `/admin/leaves` API, the system executes a multi-step conflict resolution process within a single database transaction. First, it verifies the doctor isn't already on leave. Second, it inserts the `Leave` record. Third, it queries all `CONFIRMED` appointments for that specific doctor that fall on the leave date.
The system then iterates through these affected appointments, updating their status to `CANCELLED_DUE_TO_LEAVE`. To ensure patients are promptly informed, the backend uses FastAPI's `BackgroundTasks` to queue notification jobs. These background jobs handle dispatching cancellation emails and invoking the Google Calendar API to delete the previously scheduled events, ensuring the main HTTP request remains fast and responsive.

### Notification Failure Handling
Relying on external services for email (SendGrid) and calendar integration introduces the risk of network failures or API rate limits. To handle this reliably, the background jobs should be upgraded to use a persistent task queue like Celery or RQ backed by Redis.
When an email or calendar API call fails, the task runner catches the exception and schedules a retry with exponential backoff. For critical failures that exceed the maximum retry count, the failure is logged into a dedicated `NotificationLog` table in the database with a status of `FAILED`. An admin dashboard or a cron job can then monitor these failed logs and either alert the system administrator or allow manual re-triggering of the notifications, ensuring that no patient misses a vital appointment update due to transient external errors.
