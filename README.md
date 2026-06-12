# Vanguard

Vanguard is a banking cybersecurity command center prototype for internal security operations workflows. The current implementation focuses on the Core Trust Dashboard and frontend foundation for session-wise risk monitoring.

## Current Scope

- Core React SPA foundation with Vite and Tailwind
- Shared command-center layout shell
- Global state with React Context and reducer
- Session-wise Trust Dashboard
- Active customer sessions table
- Selected-session Risk Gauge
- Selected-session status and MFA decision panel
- Selected-session behavioral trigger list
- Mock data for frontend development
- API integration contracts for future modules
- Placeholder routes for teammate-owned modules

## Features Implemented

- Session selection from Active Sessions table
- Risk logic:
  - `0-30`: Low Risk / Normal / Passkey Allowed
  - `31-70`: Medium Risk / Escalated / MFA Required
  - `71-100`: High Risk / Critical / Blocked
- Dashboard metrics:
  - Active Sessions
  - MFA Required
  - Blocked Sessions
  - Average Risk
- Enterprise dark UI suitable for a banking cybersecurity command center

## Routes

- `/` and `/login`: Operator login gateway
- `/dashboard`: Core Trust Dashboard
- `/forensics`: Document Forensics module integration area
- `/compliance`: Agentic Compliance module integration area
- `/admin`: Security/Admin module integration area

## Local Development

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173/dashboard
```

## Validation

```bash
cd frontend
npm run build
npm run lint
```

## Integration Notes

The frontend currently uses mock data only. Backend, WebSocket, ML telemetry, document forensics, compliance automation, and admin action integrations are pending.

Future modules should connect through:

- `frontend/src/lib/api-contracts.js`
- Placeholder routes in `frontend/src/App.jsx`
- Session state actions in `frontend/src/lib/store.js`
