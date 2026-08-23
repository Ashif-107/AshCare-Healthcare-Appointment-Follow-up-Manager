# System Architecture & Data Flow

This document explains how the Healthcare Appointment Manager is structured, where the API endpoints live, and how data flows seamlessly from the user's browser (Frontend) to the database and AI (Backend).

## 1. High-Level Architecture

*   **Frontend (Next.js & React):** Runs in the user's browser. It handles the UI, stores the authentication token in `localStorage`, and makes HTTP requests (using `fetch`) to the Backend.
*   **Backend (FastAPI):** Runs on your server. It receives HTTP requests, verifies the JWT tokens, reads/writes to the Supabase database using **SQLModel**, and communicates with the **Groq API** for AI summaries.
*   **Database (Supabase / PostgreSQL):** Stores all persistent data (Users, Doctors, Appointments, Leaves, Notes).

---

## 2. Backend Files & Their Roles

The backend is modularized to keep the code clean. The entry point is `backend/app/main.py`, which brings everything together.

| File Location | Purpose |
| :--- | :--- |
| `app/main.py` | The core server. It configures CORS (allowing the frontend to talk to it) and registers all the routers. |
| `app/database.py` | Establishes the connection to Supabase using the `DATABASE_URL`. |
| `app/models.py` | Defines the database tables and relationships (Schema). |
| `app/dependencies.py` | Contains security functions (like `get_current_user` and `get_admin_user`) that protect endpoints. |
| `app/services/llm.py` | Handles all communication with the Groq API. |
| `app/services/notifications.py` | Handles real background tasks including Gmail SMTP email dispatch and Google Calendar event creation/deletion using OAuth 2.0. |

### The API Routers (The Endpoints)
Instead of putting all APIs in one file, they are split by feature into the `app/routers/` folder:

1.  **`auth.py` (`/auth/*`)**: Handles user login and patient registration. It generates the JWT access token.
2.  **`admin.py` (`/admin/*`)**: Secured endpoints for the admin, specifically `POST /admin/doctors` to create new doctor accounts.
3.  **`doctors.py` (`/doctors/*`)**: Public/Patient endpoints to fetch the list of available doctors and their available time slots.
4.  **`appointments.py` (`/appointments/*`)**: The core engine. Handles placing holds on slots, confirming bookings, submitting doctor notes, and fetching a doctor's active schedule.
5.  **`leaves.py` (`/admin/leaves/*`)**: Allows admins to mark doctors as unavailable, which automatically triggers background tasks to cancel conflicting appointments.

---

## 3. Step-by-Step Data Flows

Here is exactly how the frontend and backend talk to each other during major actions.

### A. The Authentication Flow
1.  **Frontend:** User types credentials into `src/app/auth/login/page.tsx` and clicks Submit.
2.  **Frontend:** Calls `POST http://localhost:8000/auth/login` with the email and password.
3.  **Backend (`routers/auth.py`):** 
    *   Queries the `user` table to find the email.
    *   Verifies the hashed password using `passlib`.
    *   Generates a secure JWT string containing the user's ID and Role.
4.  **Frontend:** Receives the token, saves it to `localStorage`, and redirects the user to their specific dashboard based on their role.

### B. The Patient Booking Flow (With LLM)
1.  **Frontend (`src/app/patient/book/page.tsx`):**
    *   Calls `GET /doctors/` to display the list of doctors.
    *   When a doctor is selected, it calls `GET /doctors/{id}/slots` to get available times.
2.  **Frontend:** The patient types their symptoms and clicks confirm.
3.  **Frontend:** Calls `POST /appointments/confirm` sending the patient ID, doctor ID, time slot, and symptoms.
4.  **Backend (`routers/appointments.py`):**
    *   Saves the `Appointment` to the database with status `CONFIRMED`.
    *   **Data Flow to AI:** Calls `generate_pre_visit_summary(symptoms)` from `services/llm.py`.
    *   `llm.py` sends the symptoms to **Groq**. Groq returns the Urgency Level and Chief Complaint.
    *   **Database Write:** Saves the symptoms and the Groq-generated summary into the `ConsultationNote` table.
    *   **Background Task:** Tells FastAPI to run `send_booking_email()` and `create_calendar_event()` in the background. The API responds to the user instantly, while the backend securely connects to Gmail SMTP to send HTML emails and uses Google OAuth to invite users to a Google Meet calendar event.
5.  **Frontend:** Receives a success message and shows it to the patient.

### C. The Doctor Post-Visit Flow (With LLM)
1.  **Frontend (`src/app/doctor/dashboard/page.tsx`):**
    *   When the page loads, it calls `GET /appointments/doctor/{id}` to fetch active appointments.
    *   The Doctor types clinical notes and prescriptions into the text areas and clicks submit.
2.  **Frontend:** Calls `POST /appointments/{id}/post-visit` sending the notes.
3.  **Backend (`routers/appointments.py`):**
    *   Updates the `Appointment` status to `COMPLETED`.
    *   **Data Flow to AI:** Calls `generate_post_visit_summary(notes)` from `services/llm.py`.
    *   `llm.py` sends the complex clinical notes to **Groq**. Groq translates it into plain English.
    *   **Database Write:** Updates the `ConsultationNote` with the doctor's raw notes and the Groq-generated patient-friendly summary.
4.  **Frontend:** Receives the translated summary from the backend and displays it in a green success box on the screen.
