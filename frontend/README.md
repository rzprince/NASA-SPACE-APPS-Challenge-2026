# BoponX frontend — Bangladesh-first prescreening showcase

This React + TypeScript + Vite application pairs readable Bangla with English and generates a printable bilingual farm-preparation brief from validated form inputs.
Its original pointer-responsive **CSS-3D field scene** and historical precipitation
landscape are artistic/analytical visualizations, not NASA imagery or satellite maps.
There is no extra WebGL dependency. Motion is disabled for users who select
`prefers-reduced-motion`.

## Run in two terminals

From the repository root, first start FastAPI:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Then:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

The Vite dev server proxies `/api` to port 8000. Without the verified data
snapshot, the climate explorer shows an honest unavailable state. The farm form validates inputs and submits them to `POST /api/v1/plans/preview` for a deterministic **three-month preparation brief**. Choose **Print / Save as PDF** in the generated report; the browser prints the English/Bangla A4 document locally. This is not a crop prescription. Crop recommendation/rotation comparison remains deliberately blocked until agronomic sources and rules are reviewed.

## Quality gates

```powershell
npm.cmd run build
```

Test keyboard access, Bengali text wrapping, the month selector, report print/PDF, table, mobile
viewports and reduced-motion preferences. See `docs/UI_QA.md`.

Separate-host deployment needs `VITE_BOPONX_API_BASE_URL` set to the HTTPS
API origin at build time and `BOPONX_ALLOWED_ORIGINS` set to the exact web
origin on the API. PWA installation, offline service-worker support and public
hosting are not yet implemented.
