# CounterfeitGuard Frontend

React + Vite frontend for CounterfeitGuard with animated analysis, results, history, and metrics views.

## Stack
- React 18
- Vite
- TypeScript
- TailwindCSS
- framer-motion
- recharts
- lucide-react
- React Query

## Folder Layout
- `src/main.tsx`: app bootstrap
- `src/router.tsx`: route config
- `src/components/pages/`: page-level screens
- `src/lib/api.ts`: typed API client
- `src/types/`: shared frontend types

## Setup
```bash
npm install
```

## Run Dev Server
```bash
npm run dev
```

Default app URL:
- `http://localhost:5173`

## Build
```bash
npm run build
```

## Preview Production Build
```bash
npm run preview
```

## Backend Requirement
The frontend expects the FastAPI backend to be running locally:
- API base: `http://127.0.0.1:8000`

Start backend first:

```bash
cd /CounterfeitGuard/backend
source env/bin/activate
uvicorn backend.app.main:app --reload
```

## Notes
- Theme preference is stored locally.
- Metrics combine live database stats with offline validation metrics from the backend training run.
- If the SHAP plot card is empty, retrain the backend so fresh metrics are generated.
