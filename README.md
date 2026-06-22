# Vanguard

Vanguard is a banking cybersecurity command-center prototype built for internal security operations and regulatory compliance workflows. It brings together trust monitoring, document forensics placeholders, agentic compliance automation, and security/admin workflows inside a unified React + FastAPI platform.

## Current Scope

The current implementation focuses on the Core Trust Dashboard and the Member D Agentic Compliance module.

### Implemented

* React SPA foundation using Vite and Tailwind CSS
* Shared command-center layout shell
* Global state management using React Context and reducer
* Session-wise Trust Dashboard
* Active customer sessions table
* Selected-session Risk Gauge
* MFA decision/status panel
* Behavioral trigger list
* Agentic Compliance dashboard
* Manual RBI circular analysis
* TXT/PDF circular upload for analysis
* Policy reference library
* Manual/TXT/PDF reference circular ingestion
* Uploaded reference deletion for USER-REF records
* Seeded policy references locked from deletion
* Scout-style obligation extraction
* Semantic Delta-style policy gap detection
* Measurable Action Point generation
* Priority scoring
* Evidence upload and local verification
* PSO/payment-system approval circular mapping
* Offline regulatory memory fallback using local JSON storage

## Modules

### 1. Trust Dashboard

The Trust Dashboard provides a session-wise monitoring interface for banking security operators.

Risk logic:

* 0–30: Low Risk / Normal / Passkey Allowed
* 31–70: Medium Risk / Escalated / MFA Required
* 71–100: High Risk / Critical / Blocked

Dashboard metrics include:

* Active Sessions
* MFA Required
* Blocked Sessions
* Average Risk

### 2. Agentic Compliance System

The Compliance module helps a compliance officer analyze new RBI-style circulars against approved policy references.

Supported flows:

* Paste circular text manually and analyze
* Upload TXT/PDF circular and analyze
* Upload reference circulars into the policy library
* Compare new circulars against approved references
* Generate policy gaps
* Assign department-wise action points
* Produce evidence requirements
* Upload evidence for verification

The module currently supports domain-aware handling for:

* Digital fraud reporting
* PSO/payment-system approval circulars
* Cyber/CERT-In style obligations
* IT outsourcing and operational compliance references
* Evidence retention and audit workflow requirements

## Offline MVP Note

This hackathon version is designed to run in a bank-controlled offline environment. Production services such as Gemini, LangGraph, ChromaDB, and advanced Vision-AI are represented through local deterministic equivalents and JSON-backed regulatory memory. The architecture remains upgrade-ready for full production integration.

## Routes

* `/` and `/login` — Operator login gateway
* `/dashboard` — Core Trust Dashboard
* `/forensics` — Document Forensics integration area
* `/compliance` — Agentic Compliance module
* `/admin` — Security/Admin module

## Tech Stack

### Frontend

* React.js
* Vite
* Tailwind CSS
* React Context API
* Component-based dashboard architecture

### Backend

* Python
* FastAPI
* Local compliance engines
* JSON-backed regulatory memory
* PDF/TXT parsing support
* Local evidence verification logic

### Compliance Engine Components

* `scout.py` — obligation extraction and text normalization
* `delta.py` — semantic policy gap comparison
* `actions.py` — MAP/action generation
* `priority.py` — priority scoring
* `workflow.py` — compliance workflow orchestration
* `vision.py` — local evidence verification
* `chroma_store.py` — local regulatory memory fallback

## Local Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173/dashboard
```

Compliance module:

```text
http://127.0.0.1:5173/compliance
```

### Backend

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

## Validation

Frontend:

```bash
cd frontend
npm run build
npm run lint
```

Backend:

```bash
python -m compileall backend
```

## Demo Checklist

* Open Trust Dashboard and select active sessions
* Verify risk gauge and MFA decision logic
* Open Compliance module
* Load Demo Circular and analyze
* Upload a PSO/payment-system RBI PDF and analyze
* Verify complete obligations, department-wise gaps, and MAPs
* Add a reference circular to Policy Library
* Delete USER-REF reference
* Confirm seeded references remain locked
* Upload evidence for selected MAP and verify result

## Integration Notes

Future modules should connect through:

* `frontend/src/lib/api-contracts.js`
* Placeholder routes in `frontend/src/App.jsx`
* Session state actions in `frontend/src/lib/store.js`
* Compliance API client in `frontend/src/lib/compliance-api.js`

## Current Status

* Trust Dashboard: Functional frontend foundation
* Compliance Module: Functional offline MVP
* Document Forensics: Integration area available
* Security/Admin: Integration area available
* Full production integrations: Pending team merge and final deployment
