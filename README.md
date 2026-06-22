# Member A + Member D Module README

## Vanguard — Trust Dashboard and Agentic Compliance Module

This document covers the implemented work for **Member A** and **Member D** in the Vanguard/SURAKSHA banking cybersecurity command-center prototype.

Member A focuses on the **Trust Dashboard and frontend foundation**, while Member D focuses on the **Agentic Compliance System** for RBI circular analysis, policy gap detection, MAP generation, and evidence verification.

---

# Member A — Trust Dashboard + Core Frontend Foundation

## Overview

Member A builds the core React frontend foundation and Trust Dashboard for Vanguard. This module provides the main command-center layout, route structure, session-wise monitoring dashboard, selected-session risk gauge, MFA decision panel, and behavioral trigger list.

The Trust Dashboard acts as the visual control center for behavioral identity and adaptive MFA workflows.

## Responsibilities

* Set up the React + Vite frontend foundation
* Configure Tailwind CSS styling
* Build shared command-center layout
* Create dashboard navigation shell
* Implement global state using React Context and reducer
* Display active customer sessions
* Show selected-session risk score
* Display MFA decision based on risk level
* Display behavioral anomaly triggers
* Provide placeholder routes for teammate modules

## Features Implemented

### Core Frontend Foundation

* React SPA using Vite
* Tailwind CSS styling
* Shared layout shell
* Sidebar navigation
* Modular route structure
* Global state management through Context API

### Trust Dashboard

* Active customer sessions table
* Session selection flow
* Risk Gauge component
* Session status panel
* MFA decision panel
* Behavioral trigger list
* Dashboard metrics cards

## Risk Decision Logic

| Risk Score | Status                  | Decision        |
| ---------- | ----------------------- | --------------- |
| 0–30       | Low Risk / Normal       | Passkey Allowed |
| 31–70      | Medium Risk / Escalated | MFA Required    |
| 71–100     | High Risk / Critical    | Session Blocked |

## Member A Important Files

```text
frontend/src/pages/Dashboard.jsx
frontend/src/pages/Login.jsx
frontend/src/components/ui/Layout.jsx
frontend/src/components/dashboard/RiskGauge.jsx
frontend/src/components/dashboard/TriggerList.jsx
frontend/src/components/dashboard/SessionStatus.jsx
frontend/src/lib/store.js
frontend/src/lib/api-contracts.js
frontend/src/App.jsx
```

## Member A Current Status

* Frontend foundation: Completed
* Trust Dashboard: Completed
* Mock session monitoring: Completed
* Placeholder module routes: Completed
* Real backend WebSocket telemetry: Pending Member C integration
* Real Isolation Forest scoring: Pending Member C backend integration
* Real privacyIDEA/WebAuthn MFA: Pending Member E integration

---

# Member D — Agentic Compliance System

## Overview

Member D builds Vanguard’s Agentic Compliance module. This module helps compliance officers analyze new RBI-style circulars, compare them against approved policy references, detect policy gaps, generate department-wise Measurable Action Points, assign priority scores, and verify implementation evidence.

The module is designed as an offline, bank-controlled MVP for regulatory intelligence and compliance workflow automation.

## Responsibilities

* Build compliance backend engines
* Implement circular text parsing and obligation extraction
* Compare new circulars with approved policy references
* Generate policy gaps
* Generate Measurable Action Points
* Assign priority scores
* Verify uploaded evidence
* Build compliance API routes
* Build Compliance dashboard UI
* Support manual, TXT, and PDF circular analysis
* Support policy reference upload and deletion

## Features Implemented

### Circular Analysis

* Manual circular paste and analysis
* TXT/PDF circular upload for analysis
* Text-based PDF extraction using local parser
* Safe scanned/image-only PDF rejection
* Normalized response shape for frontend consumption

### Policy Reference Library

* Seeded approved references
* Manual reference circular entry
* TXT/PDF reference upload
* Local regulatory memory storage
* Preview text for UI display
* Full text retained for comparison
* USER-REF deletion support
* Seeded references locked from deletion

### Compliance Intelligence

* Scout-style obligation extraction
* Semantic Delta-style gap detection
* Domain-aware reference matching
* Priority scoring on 1–10 scale
* Department/business vertical assignment
* Measurable Action Point generation
* Evidence requirement generation
* Local evidence verification

## Supported Compliance Domains

* Digital fraud reporting
* PSO/payment-system prior approval circulars
* Cyber/CERT-In incident obligations
* IT outsourcing compliance
* Evidence retention and audit obligations
* General regulatory workflow obligations

## Member D Important Backend Files

```text
backend/api/compliance.py
backend/engines/compliance/scout.py
backend/engines/compliance/delta.py
backend/engines/compliance/actions.py
backend/engines/compliance/priority.py
backend/engines/compliance/workflow.py
backend/engines/compliance/vision.py
backend/engines/compliance/chroma_store.py
backend/scripts/seed_chroma.py
backend/data/compliance/regulatory_memory.json
```

## Member D Important Frontend Files

```text
frontend/src/pages/Compliance.jsx
frontend/src/lib/compliance-api.js
frontend/src/components/compliance/AgentWorkflow.jsx
frontend/src/components/compliance/CircularCompare.jsx
frontend/src/components/compliance/EvidenceUpload.jsx
```

## Compliance API Routes

| Endpoint                                          | Purpose                                 |
| ------------------------------------------------- | --------------------------------------- |
| `GET /api/compliance/health`                      | Compliance service health check         |
| `POST /api/compliance/analyze`                    | Analyze manually pasted circular text   |
| `POST /api/compliance/analyze/upload`             | Analyze TXT/PDF circular upload         |
| `GET /api/compliance/circulars`                   | List circular/reference records         |
| `POST /api/compliance/references`                 | Add manual reference circular           |
| `POST /api/compliance/references/upload`          | Add TXT/PDF reference circular          |
| `DELETE /api/compliance/references/{circular_id}` | Delete uploaded USER-REF reference      |
| `POST /api/compliance/evidence/verify`            | Verify uploaded implementation evidence |
| `GET /api/compliance/actions`                     | Fetch generated compliance actions      |

## Member D Current Status

* Manual circular analysis: Completed
* TXT/PDF circular upload analysis: Completed
* Reference circular upload: Completed
* Uploaded reference deletion: Completed
* Seeded reference locking: Completed
* Digital fraud demo flow: Completed
* PSO/payment-system circular mapping: Completed
* Evidence verification: Completed as local MVP
* Real Gemini/LangGraph/ChromaDB production services: Upgrade-ready, not active in offline MVP

---

# Shared Routes

| Route         | Purpose                             |
| ------------- | ----------------------------------- |
| `/`           | Operator login gateway              |
| `/login`      | Operator login gateway              |
| `/dashboard`  | Core Trust Dashboard                |
| `/forensics`  | Document Forensics integration area |
| `/compliance` | Agentic Compliance module           |
| `/admin`      | Security/Admin integration area     |

---

# Local Development

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173/dashboard
http://127.0.0.1:5173/compliance
```

## Backend

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

---

# Validation

## Backend

```bash
python -m compileall backend
```

## Frontend

```bash
cd frontend
npm run build
npm run lint
```

---

# Demo Checklist

## Member A Demo

1. Open `/dashboard`
2. Select a customer session from the active sessions table
3. Observe risk score update
4. Review MFA decision
5. Review behavioral anomaly triggers
6. Navigate to Forensics, Compliance, and Admin routes

## Member D Demo

1. Open `/compliance`
2. Load Demo Circular and analyze
3. Review summary and key obligations
4. Review First Gap Preview
5. Review policy gaps
6. Review department-wise MAPs
7. Upload implementation evidence
8. Add a reference circular through Policy Reference Library
9. Upload a PSO/payment-system PDF circular
10. Verify PSO-specific obligations, owners, gaps, and MAPs

---

# Offline MVP Note

This hackathon version is designed to run in a bank-controlled offline environment. Production services such as Gemini, LangGraph, ChromaDB, and advanced Vision-AI are represented through local deterministic equivalents and JSON-backed regulatory memory.

The architecture remains upgrade-ready for production integration with:

* Gemini for semantic extraction and multimodal reasoning
* LangGraph for stateful multi-agent orchestration
* ChromaDB for persistent vector memory
* OCR/Vision pipelines for scanned document processing

---

# Known Limitations

* Trust Dashboard currently uses mock session data
* Real WebSocket telemetry integration is pending Member C
* Real privacyIDEA/WebAuthn integration is pending Member E
* No OCR for scanned PDFs
* No live RBI/SEBI fetching
* No external LLM API calls in offline demo
* JSON-backed regulatory memory is used instead of live ChromaDB server
* Evidence verifier uses local deterministic checks instead of real Gemini Vision
