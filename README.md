# ATS Resume Builder

A zero-cost, AI-driven Applicant Tracking System (ATS) resume builder.

**Stack:** Python 3.13 · Django 6.0 (native Tasks API + `django-tasks` DB backend) · Google Gemini (free tier) · pypdf · SQLite

## Local development (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env   # then fill in SECRET_KEY and GEMINI_API_KEY
python manage.py migrate
python manage.py runserver
```