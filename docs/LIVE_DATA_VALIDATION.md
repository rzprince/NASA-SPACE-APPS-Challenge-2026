# Live NASA POWER validation gate

This workflow uses an internet-connected GitHub Actions runner to acquire the
first NASA POWER pilot dataset from the documented upstream API. It does **not**
manufacture or commit climate measurements, and it has no access to secrets or
write permissions for the repository.

## Run

After the workflow is merged, open GitHub **Actions → NASA POWER live pilot
validation → Run workflow**. The initial feature-branch push also triggers the
same one-time validation. Inspect the workflow log for original request metadata,
variable units, source-product metadata, geographic information, year coverage,
and raw SHA-256 checksum.

If it succeeds, download its 14-day artifact
`boponx-nasa-power-rajshahi-2024`; it contains the original response and the
processed climate snapshot. Extract into the repository's ignored `data/raw/`
and `data/processed/` folders, maintaining the archive directories. Start
FastAPI and the frontend as documented in the root README. The climate UI
will only render the processed snapshot if the API recognizes it as
`nasa_power_https` and the schema/location/source URL pass its gate.

If NASA responds with a validation error, timeout or incomplete time series,
the workflow **fails**. Review the exact NASA response and adjust the pipeline
in a new reviewed change; never replace failing values with sample numbers.

## Scientific review gate

A green workflow is a technical ingestion test, **not** independent evidence
that gridded POWER values represent a farmer's field or that a rotation is
agronomically suitable. Confirm variable definitions, spatial resolution,
date/time convention, quality, and approved usage before public claims.

NASA reference: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
