# Vanguard Frontend

React + Vite + Tailwind frontend for Vanguard, a banking cybersecurity command center prototype.

The current frontend scope is the Core Trust Dashboard and foundation routes for future module integration.

## Run Locally

```bash
npm install
npm run dev
```

## Available Scripts

- `npm run dev`
- `npm run build`
- `npm run lint`
- `npm run preview`

## Notes

Mock data is currently used for the dashboard. Future backend and teammate modules should connect through `src/lib/api-contracts.js`, `src/lib/store.js`, and the placeholder routes.
