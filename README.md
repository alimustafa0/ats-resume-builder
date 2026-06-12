# ATS Resume Builder

A zero-cost, AI-driven web app that parses your résumé and a job posting, scores how well they match, and tailors your résumé into a clean, ATS-friendly PDF — without inventing anything you didn't actually do.

Built with Django 6 and Google's Gemini, using only free-tier and open-source components.

![Python](https://img.shields.io/badge/python-3.13-blue)
![Django](https://img.shields.io/badge/django-6.0-092e20)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Résumé parsing** — Upload a PDF; it's extracted and structured (contact, summary, experience, education, skills) by an LLM with a strict schema.
- **Job posting parsing** — Paste any posting; it's distilled into required skills, preferred skills, responsibilities, qualifications, and keywords.
- **Match scoring** — A transparent 0-100 score with a required/preferred gap breakdown, combining deterministic keyword coverage with an LLM judge that credits synonyms and demonstrated experience.
- **Faithful tailoring** — Rephrases and re-emphasizes your real experience toward a specific role. It never fabricates, inflates, or changes your employers, titles, dates, or numbers.
- **ATS-friendly PDF export** — Single-column, standard-font, parser-safe PDF generated with ReportLab.
- **Async processing** — Parsing runs in a background worker, so uploads never block; the UI updates live via HTMX.
- **Accounts & ownership** — Email-based authentication; every résumé, posting, and match is scoped to its owner.

## How it works

```
PDF résumé ──▶ text extraction (pypdf) ──▶ structured data (Gemini + Pydantic schema)
job posting ─▶ structured requirements (Gemini + Pydantic schema)
                                   │
                                   ▼
                  deterministic coverage  ──▶  LLM judge rescues gaps
                                   │
                                   ▼
                     score (0-100) + required/preferred breakdown
                                   │
                                   ▼
        faithful tailoring (Gemini) ──▶ ATS-friendly PDF (ReportLab)
```

Each long-running step (parsing, scoring, tailoring) is queued as a background task and reported back to the browser through HTMX polling.

## Tech stack

- **Backend:** Python 3.13, Django 6.0
- **AI:** google-genai SDK (Gemini 2.5 Flash-Lite), structured output via Pydantic schemas
- **Background tasks:** Django tasks framework with the django-tasks-db backend
- **PDF:** ReportLab (generation), pypdf (extraction)
- **Frontend:** Django templates + HTMX, custom iOS-inspired CSS
- **Config:** python-decouple (12-factor environment variables)
- **Database:** SQLite (development), PostgreSQL-ready (production)

## Project structure

```
ats-resume-builder/
├── config/
│   └── settings/
│       ├── base.py            # shared settings
│       ├── development.py     # DEBUG=True (manage.py default)
│       └── production.py      # DEBUG=False, security hardening
├── apps/
│   ├── accounts/              # custom email-based user, auth views
│   ├── core/                  # base templates, shared services, dashboard
│   ├── resumes/               # résumé model, extraction, rendering, tailoring
│   ├── jobs/                  # job posting model and extraction
│   └── matching/              # scoring, semantic judge, match results
├── requirements.txt
├── .env.example
└── manage.py
```

The interesting logic lives in each app's `services/` package — extraction, scoring, semantic judging, PDF rendering, and tailoring are plain, testable functions kept out of the views.

## Getting started

### Prerequisites

- Python 3.13+
- A Gemini API key (free from [Google AI Studio](https://aistudio.google.com/app/apikey))

### Setup

```bash
# 1. Clone
git clone https://github.com/alimustafa0/ats-resume-builder.git
cd ats-resume-builder

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env          # Windows
# cp .env.example .env           # macOS / Linux
# then open .env and fill in the values

# 5. Apply migrations
python manage.py migrate

# 6. Create an admin user (optional, for /admin)
python manage.py createsuperuser
```

### Environment variables

Set these in your `.env` file (see `.env.example`):

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Django secret key. Generate a fresh, random value. |
| `GEMINI_API_KEY` | Yes | Your Google Gemini API key. |

`DJANGO_SETTINGS_MODULE` defaults to `config.settings.development` via `manage.py`; set it to `config.settings.production` in deployment.

## Running

The app needs two processes: the web server and the background worker.

```bash
# Terminal 1 — web server
python manage.py runserver

# Terminal 2 — background task worker
python manage.py db_worker
```

Open http://127.0.0.1:8000.

Without the worker running, uploads and postings stay in the "processing" state, because the parsing tasks are never picked up.

## Usage

1. **Sign up** with your email.
2. **Upload a résumé** (PDF). It's parsed in the background; the page updates when it's ready.
3. **Add a job posting** by pasting its text. It's parsed the same way.
4. **Run a match** — pick a parsed résumé and a parsed posting to get a score and a gap breakdown.
5. **Tailor** your résumé to that posting, then **download** the ATS-ready PDF.

## Design notes

A few deliberate engineering choices:

- **Two-stage scoring.** A fast, deterministic token-coverage pass produces an explainable baseline; an LLM judge then runs only over the *missing* items to credit synonyms, category matches, and skills demonstrated through experience. Embedding similarity was evaluated first, but cosine scores clustered too tightly to set reliable thresholds.
- **Honest tailoring.** The tailoring prompt is hardened against the usual LLM failure mode of quietly promoting you to "Senior" or inventing achievements. Employers, titles, dates, education, and every quantified metric are preserved verbatim; the posting only dictates *emphasis*, not identity. The output is best treated as a strong first draft for human review.
- **ATS-first PDF.** Résumés render as a single column with standard fonts and no tables, multi-column layouts, or images, so applicant-tracking parsers read them in the right order. ReportLab was chosen over HTML-to-PDF engines partly because it is pure Python and installs cleanly on Windows.
- **Async by default.** Every model call happens in a background worker, so a slow or rate-limited API never blocks a web request; the browser polls for state with HTMX.
- **Zero cost.** Everything uses free-tier or open-source components and runs without a credit card.

## Roadmap

- Deployment to a free-tier host with managed PostgreSQL
- Richer separation of true skills vs. qualifications in posting analysis
- Optional dark mode

## License

Released under the MIT License. See `LICENSE` for details.