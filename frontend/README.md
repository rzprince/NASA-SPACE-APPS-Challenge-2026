# BoponX web — milestone 02

The first React + TypeScript interface implements a mobile-first climate viewer and
a farm-input validation form. It intentionally **does not** display crop-rotation
recommendations before local agricultural rules are source-reviewed.

## Start locally

Run FastAPI first from the repository root:

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local Vite URL printed in the terminal (normally port 5173). Vite proxies
`/api` to FastAPI on port 8000. For a separately hosted backend set
`VITE_BOPONX_API_BASE_URL` to its HTTPS origin when building the frontend and
`BOPONX_ALLOWED_ORIGINS` to the exact frontend origin when starting the API.
Do not set permissive wildcard CORS for a public deployment.

## Data readiness

By default the regional climate panel shows `DATASET_UNAVAILABLE`. To populate
it, execute the NASA POWER acquisition command in the root README on a machine
with internet access and inspect the provider metadata. Test-only or local
unverified inputs are refused by the API. No sample climate numbers are
substituted.

The farm form validates soil pH, location, irrigation status and priority input;
it does not persist personal farm records or evaluate crop compatibility.
The rotation comparison remains explicitly pending.

The interface is responsive but **PWA install/offline shell and full Bangla
localization are not yet implemented**. The lockfile should be generated and
committed after the first successful online dependency installation.
