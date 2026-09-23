# SmartCampus AI — Hackathon MVP

A beginner-friendly Smart Education prototype for the DCGC2.0 Hack Sprint.

## Features
1. Assignment/deadline tracker
2. College notice summarizer
3. AI-style study planner
4. Campus assistant chatbot
5. Student dashboard

## Run locally

Install Python 3.11+.

```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open:
http://127.0.0.1:5000

## Google Cloud / Cloud Run

This repository includes a Dockerfile for Cloud Run.

Build and deploy after creating/selecting a Google Cloud project and enabling Cloud Run:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud run deploy smartcampus-ai --source . --region asia-south1 --allow-unauthenticated
```

### Important production note
The demo uses SQLite for simplicity. SQLite data inside a Cloud Run container is not a persistent production database. For the final cloud version, replace the SQLite layer with Firestore or Cloud SQL.

## Suggested hackathon demo
1. Open dashboard.
2. Add an assignment.
3. Paste a college notice and summarize it.
4. Generate a 5-day study plan.
5. Ask the Campus Assistant a question.
6. Explain the architecture and show the Cloud Run deployment.

## Team roles
- Frontend/UI
- Python/backend
- AI/feature integration
- Cloud/deployment + presentation

## Next upgrades
- Firebase Authentication
- Firestore database
- Gemini API for richer AI answers
- Teacher/admin notice upload
- Email/WhatsApp-style reminders
- Student login and personalized dashboards
