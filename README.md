# BoponX · বপনএক্স
### From Space to Soil · মহাকাশ থেকে মাটিতে

**Team EARTH.exe · Bangladesh · NASA Space Apps Challenge 2026 · Field Shift: Adapting Farms with NASA Data**

BoponX is an independent, bilingual, mobile-first **crop-rotation decision-support project**. It is designed to connect documented NASA environmental context, local soil and crop information, and farmer priorities so farmers can explore multi-season strategies. We are building a tool to *inform* farmers—not automate agricultural decisions or promise yields.

**Prescreening preview:** This repository implements a Bangladesh-first animated CSS-3D landing experience, a public-domain Natural Earth-based 3D country silhouette, a verified NASA historical climate explorer, and **a working farm → three-month bilingual preparation brief → browser Print / Save as PDF flow**. The brief personalizes a *recording, testing and extension-consultation routine* from farmer inputs and displays the corresponding actual **2024 historical** regional monthly reference. **It is not a crop prescription, 2026–27 weather forecast or scientifically approved rotation.** Local agronomic constraints and direct satellite-observation integration remain development gates.

> BoponX is a Team EARTH.exe entry. NASA POWER is a data provider; NASA and its partners have not endorsed this application. The original 3D artwork is conceptual, not NASA imagery or an actual satellite view of Rajshahi.

## What works now

| Implemented and reproducible | Not yet implemented / not claimed |
| --- | --- |
| Responsive English + Bangla UI; CSS-3D farm hero, Bangladesh silhouette and historical-rainfall landscape | Native Android app, nationwide farm coverage, complete localization of all system messages |
| 2024 NASA POWER temperature and precipitation pilot data; daily and coverage-aware monthly views | Forecasts, long-term climate-trend conclusions, direct satellite-observation integration |
| Original NASA request link, source products, time convention, coverage and SHA-256 snapshot identity | Farm-specific sensor readings or satellite-based field soil tests |
| Farm validation and personalized, printable bilingual three-month **preparation/monitoring** routine with explicit unknowns | Reviewed crop catalog, crop-specific planting calendar, automatic rotation engine, water saving or yield estimates |
| Offline-capable *local demonstration* after installing dependencies and copying the approved dataset | Installable offline PWA, public production deployment and synchronized multi-farm accounts |

### Generate and save your bilingual three-month report

1. Open **My plan / আমার পরিকল্পনা** (or scroll to the farm form). Enter your known farm details, planning **start month and year**, optionally a crop you are considering, and your priority.
2. Choose **Generate my 3-month brief / আমার তিন মাসের নোট তৈরি করুন**. The API validates inputs, reads the locally verified NASA snapshot and returns a deterministic **three-month preparation checklist**, not crop-specific advice. The report appears below the form automatically.
3. Review the three months, tick tasks as you complete them, and choose **Print / Save as PDF / প্রিন্ট / PDF হিসেবে সংরক্ষণ**. In the print dialog select **Save as PDF**; on Android use **Print → Save as PDF**. The printable layout is A4 and preserves both English and Bangla in the browser’s own text renderer.

**Important:** The API does not save the submitted profile. A PDF is saved on *your own device* only when you explicitly print/save it. The 2024 historical rainfall and temperature beside each planned month are *reference values from a different year*, never a predicted value for the planning month. The routine asks users to log actual field conditions, confirm soil/irrigation information and consult a local agricultural adviser. It **does not choose a crop, prescribe sowing dates or generate a validated three-season rotation**.

### Scientifically bounded demonstration

The provisional reference point is **24.37° N, 88.60° E, near Rajshahi**. It is *not* the position of a surveyed farm. The pinned dataset is **NASA POWER Daily API, 1 January–31 December 2024, T2M and PRECTOTCORR, Agroclimatology community, LST days**. The returned meteorological source is **MERRA-2 reanalysis**, at native gridded resolution; it is not direct field observation or a next-season prediction. All 366 requested dates passed the initial completeness checks. The original raw-data SHA-256 is:

```text
512420f8cd947e21a84aa1e43292674be7e047fadfbcdd4ae4b3684647726495
```

Monthly rainfall totals are shown only when every daily value needed for the month is present. Incomplete months yield an explicit unavailable state, not interpolated measurements. See [evidence and methodology](docs/EVIDENCE_REGISTER.md).

## Start on Windows (PowerShell)

**Prerequisites:** Python 3.12 is the tested CI version (another Python version may also work), Node.js, npm and the verified NASA data ZIP. Run commands from the repository folder containing `README.md`. The `PS C:\...>` terminal prompt is **not** part of a command.

**1. Put the data in place.** Extract the approved [GitHub Actions dataset artifact](https://github.com/rzprince/NASA-SPACE-APPS-Challenge-2026/actions/runs/35860018103), or the previously downloaded `BoponX_NASA_POWER_Rajshahi_2024.zip`, so its two files are located at:

```text
data/raw/power_512420f8cd947e21a84aa1e43292674be7e047fadfbcdd4ae4b3684647726495.json
data/processed/power_rajshahi-pilot_20240101_20241231.json
```

The raw and processed artifacts are deliberately not committed to Git. GitHub Actions artifacts can expire; the acquisition command below can recreate a **new, separately reviewed** dataset. Do not label a changed response as the pinned snapshot.

**2. Start the API in the first terminal.**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q backend\tests
.\.venv\Scripts\python.exe -m scripts.verify_pilot
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/api/v1/health` for `"climate_snapshot_ready": true`. The additional verification script recalculates the processed climate data from the pinned raw response and checks its hash.

**3. Start the web app in a second terminal.**

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open the local address printed by Vite (usually `http://localhost:5173`). Use `npm.cmd` when PowerShell blocks `npm.ps1`. **Keep both terminals open.** The dev server proxies `/api` to the local API.

On macOS/Linux, use `python3 -m venv .venv`, `.venv/bin/python` instead of `.\.venv\Scripts\python.exe`, and `npm` instead of `npm.cmd`.

### If the data ZIP is unavailable

With an internet connection and from the repository root, run:

```powershell
.\.venv\Scripts\python.exe -m data.acquisition.power --location rajshahi-pilot --latitude 24.37 --longitude 88.60 --start 20240101 --end 20241231
```

Review the response metadata and SHA-256. NASA POWER data can be revised; if the hash differs from the pinned value, the current verification command will **fail intentionally** until the new snapshot is independently reviewed and the manifest/verification baseline is updated.

## Demo route and APIs

The intended **prescreening demo** is: original CSS-3D farm hero → Bangladesh atlas with accurate pilot pin → verified historical NASA climate → select rainfall/temperature month → inspect source and coverage → enter farm context and planning window → generate an actual bilingual three-month preparation report → use Print / Save as PDF → explain what reviewed crop-specific recommendations still require. No fabricated recommendation is staged.

| API | Status |
| --- | --- |
| `GET /api/v1/health` and `GET /api/v1/locations` | Implemented |
| `GET /api/v1/climate/rajshahi-pilot` | Implemented; requires validated local snapshot |
| `GET /api/v1/climate/rajshahi-pilot/monthly` | Implemented; deterministic monthly aggregation |
| `POST /api/v1/farms/validate` | Implemented; user inputs are not independently verified |
| `POST /api/v1/plans/preview` | Implemented: deterministic three-month **preparation brief**, historical reference and missing-input flags; no agronomic prescription |
| `GET /api/v1/crops` | Empty until local crop rules are source-reviewed |
| `POST /api/v1/rotations/compare` | Deliberately returns `AGRONOMIC_RULES_NOT_APPROVED` until reviewed |

Run `python -m pytest -q backend/tests` and `cd frontend && npm.cmd run build` for regression checks. GitHub Actions executes both on code changes.

## Team, sources and submission

- [October 1 prescreening and 240-second demo plan](docs/OCTOBER_1_PRESCREEN.md)
- [NASA and Bangladesh evidence register](docs/EVIDENCE_REGISTER.md)
- [UI quality and accessibility checklist](docs/UI_QA.md)
- [AI-use disclosure](docs/AI_USE.md)
- [Current implementation status](docs/IMPLEMENTATION_STATUS.md)

Challenge brief: https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/  
NASA POWER daily API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/  
NASA POWER data references: https://power.larc.nasa.gov/docs/referencing/  

Software is offered under the [MIT License](LICENSE). The Bangladesh cartographic silhouette adapts the public-domain Natural Earth 1:110m countries layer; it is illustrative, not a surveyed field map. That software license **does not relicense** NASA data, third-party agricultural resources, satellite imagery, fonts or other external assets. Every additional dataset requires source, permission and attribution review.

**Team EARTH.exe:** Rezwan Hossain Prince (project lead), MD. Khairul Islam (QA/operations), Md. Siam Rayhan (application), Iftekhar Azad Ether (data/algorithms), Tulip Mondal (agricultural and source research). Project name **BoponX** has no association with SpaceX. The full challenge materials and local submission instructions should be rechecked when released.
