# GCUL Papers — Full Setup Guide

## Architecture Overview

```
[User Browser]
     │
     ├── Google Login  →  Supabase Auth (free)
     ├── Upload PDF    →  FastAPI Backend (Render, free)
     │                        │
     │                        ├── PDF File  →  GitHub Repo (free storage)
     │                        └── Metadata →  Neon PostgreSQL (free)
     └── View Papers   →  FastAPI GET /papers
```

## File Structure

```
gcul-papers/
│
├── backend/
│   ├── main.py          ← FastAPI app entry point
│   ├── config.py        ← All environment variables
│   ├── database.py      ← Neon DB connection
│   ├── models.py        ← DB table definitions
│   ├── github.py        ← GitHub file upload logic
│   ├── routes/
│   │   ├── papers.py    ← GET /papers, POST /upload
│   │   └── auth.py      ← verify Google token
│   ├── requirements.txt
│   └── .env             ← your secrets (never commit this)
│
└── frontend/
    ├── index.html
    ├── style.css
    ├── script.js        ← main app
    ├── auth.js          ← Google login logic
    ├── upload.js        ← upload form logic
    └── config.js        ← API base URL (one place)
```

---

## STEP 1 — Neon Database Setup

1. Go to neon.tech → open your project
2. Open SQL Editor → run this:

```sql
CREATE TABLE papers (
  id          SERIAL PRIMARY KEY,
  subject     TEXT NOT NULL,
  semester    INTEGER NOT NULL,
  year        INTEGER NOT NULL,
  type        TEXT NOT NULL,
  department  TEXT NOT NULL,
  pdf_url     TEXT NOT NULL,
  uploaded_by TEXT,
  status      TEXT DEFAULT 'approved',
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

3. Copy your connection string from Dashboard → it looks like:
   postgresql://user:password@host/dbname

---

## STEP 2 — GitHub Token Setup

1. GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained
2. Give access to your papers repo
3. Permissions: Contents = Read & Write
4. Copy the token

---

## STEP 3 — Google OAuth Setup

1. Go to console.cloud.google.com
2. Create project → APIs & Services → Credentials
3. Create OAuth 2.0 Client ID → Web Application
4. Authorized origins: add http://localhost:5500 (dev) + your GitHub Pages URL
5. Copy Client ID

---

## STEP 4 — Backend Setup & Deploy to Render

1. Create a new GitHub repo for backend (e.g. gcul-backend)
2. Push all backend/ files to it
3. Go to render.com → New Web Service → connect that repo
4. Set environment variables in Render dashboard (from your .env)
5. Deploy

---

## STEP 5 — Frontend Setup

1. In frontend/config.js → set your Render backend URL + Google Client ID
2. Push frontend to your existing GitHub Pages repo
3. Done!

---

## STEP 6 — Adding Papers Manually (still works)

You can still add papers directly via SQL in Neon dashboard:

```sql
INSERT INTO papers (subject, semester, year, type, department, pdf_url, uploaded_by)
VALUES ('Computer Networks', 6, 2024, 'Final Term', 'BSCS', 'https://...', 'admin');
```