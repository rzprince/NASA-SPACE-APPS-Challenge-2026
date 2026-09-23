# BoponX — From Space to Soil

**Team EARTH.exe · NASA Space Apps Challenge 2026 · Field Shift: Adapting Farms with NASA Data**

BoponX is an evidence-first, mobile-first crop-rotation decision-support project. The proposed product combines NASA environmental data, documented crop and local-soil information, and farmer priorities to compare feasible multi-season crop sequences. It is **not** an agricultural forecasting or farm-specific soil-testing system.

## Implementation status (23 September 2026)

**Implemented:** NASA POWER daily acquisition/validation, a versioned processed-data format, FastAPI health/location/climate endpoints, farm-input validation, mobile-first React climate viewer, source-evidence display, and offline backend tests. **Not yet implemented:** source-reviewed crop-rule catalog, rotation comparison engine, direct-EO integration, installable PWA, public deployment, and farmer-facing agricultural advice. A real 2024 NASA POWER snapshot was acquired and validated by GitHub Actions on 23 September 2026; it is available as a downloadable workflow artifact, **not** committed to Git. The app displays an explicit unavailable state until the validated files are placed in the local data directory. The returned POWER source metadata identifies MERRA2 reanalysis, not a direct satellite observation; direct EO integration remains a separate gate.

## Start the backend

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\\Scripts\\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`. Until the NASA pipeline has been run, the climate route intentionally returns HTTP 503 with a data-not-ready message; it never displays invented values.

## Start the frontend

In a second terminal from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (typically `http://localhost:5173`). The dev server proxies `/api` to FastAPI on port 8000. Without a verified NASA snapshot the climate screen reports that data are unavailable, while the farm-input form can be validated through the API. A source-reviewed crop-rotation comparison is **not yet implemented**. See `frontend/README.md` for separate-origin deployment settings.

## Acquire the initial NASA climate snapshot

From the repository root, with internet access:

```bash
python -m data.acquisition.power --location rajshahi-pilot --latitude 24.37 --longitude 88.60 --start 20240101 --end 20241231
```

The coordinate is an **illustrative regional reference point**, not a surveyed farm. The command requests the NASA POWER agroclimatology daily parameters `T2M` and `PRECTOTCORR` with explicit local-solar-time (`LST`) days. It saves an immutable raw response and a validated, provenance-tagged summary under ignored `data/raw/` and `data/processed/`. An already processed snapshot is reused; use `--refresh` to request a new one deliberately. On a network error it exits rather than creating synthetic NASA data.

The route `GET /api/v1/climate/rajshahi-pilot` becomes available after a successful acquisition using the specified date range. Use `BOPONX_DATA_ROOT=/path/to/data` to change the data directory.

**Verified data shortcut:** The [successful NASA POWER validation run](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026/actions/runs/35860018103) includes the `boponx-nasa-power-rajshahi-2024` artifact (raw response + validated processed snapshot). Download the artifact ZIP and extract it into this repository's `data/` directory so that `data/raw/` and `data/processed/` are populated; then start the backend. The ZIP is not a crop recommendation, a farm measurement, or a live forecast.

## Run tests without NASA network access

```bash
pip install -r backend/requirements-dev.txt
python -m pytest -q backend/tests
```

The tests use clearly synthetic, in-memory POWER-shaped payloads and temporary files. Those samples are **not** NASA observations and are never shipped as a farmer-facing demonstration dataset.

## Scientific and submission boundaries

- The POWER point time series is regional/gridded context, not a measurement at a particular farm.
- A historical indicator is not a next-season forecast.
- Soil and crop constraints require local, source-reviewed references before recommendations can be enabled.
- No yield, water-saving, or soil-health benefit estimate is implemented or claimed.
- A directly sensed NASA Earth-observation product (proposed: GPM IMERG) must pass a separate feasibility gate before any integration claim.

See `docs/DATA_SOURCES.md` and `docs/IMPLEMENTATION_STATUS.md`.

**Repository:** https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026
