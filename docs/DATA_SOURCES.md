# BoponX data source register — initial milestone

| Source | Role | Status | Reference |
| --- | --- | --- | --- |
| NASA POWER daily point API | Historical daily T2M and PRECTOTCORR; local solar time | Acquisition script and tests implemented; **live download not yet executed in this environment** | https://power.larc.nasa.gov/docs/services/api/temporal/daily/ |
| NASA GPM IMERG | Candidate direct satellite-based precipitation for event build | Feasibility and quality review pending; **not integrated** | https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGDF_07/summary |
| NASA SMAP | Candidate regional surface-soil-moisture context | Deferred; **not a farm soil test** | https://nsidc.org/data/spl3smp_e/versions/6 |
| Local crop/soil knowledge | Reviewed crop calendars, rotations and soil constraints | Research and redistribution permission pending; **no crop recommendation is implemented** | https://barcapps.gov.bd/cropzoning/homes/intro |

## NASA POWER ingestion contract

`T2M` and `PRECTOTCORR` are requested for the explicit latitude, longitude, date range, AG community and LST convention. The validator requires provider-supplied units. It preserves response geometry, raw SHA-256, source products, API metadata and the precise request URL. Fill/missing values remain null. A full-period precipitation total is null if even one date is invalid; valid-day sums and coverage are shown separately.

The Rajshahi coordinate is a provisional *regional reference point*, not surveyed farm coordinates. The API does not claim POWER values measure conditions in one farmer's field. Historical records are not predictions. Raw NASA data are excluded from the repository until successfully acquired and licensing/size reviewed. Synthetic test payloads stay only in test code.
