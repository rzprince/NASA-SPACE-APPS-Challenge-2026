# BoponX evidence register and scientific boundary
**Reviewed:** 26 September 2026

BoponX separates evidence by meaning. A satellite/reanalysis value must never be silently promoted into a field measurement, soil test or crop recommendation.

## Challenge frame

The official 2026 Field Shift summary asks for a decision-support tool using NASA Earth observations together with local soil information, crop characteristics and farmer priorities to help farmers explore crop-rotation strategies for soil health and adaptation.

BoponX implements the evidence pipeline now and keeps the final crop-rotation recommendation layer gated until the local agronomic rules are sourced and reviewable.

Source:
https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/

## GPM IMERG Early V07B

Current NASA documentation:
- coverage: January 1998–present
- current algorithm: V07B
- minimum latency: about 4 hours
- spatial resolution: 0.1 degree / about 10 km
- 30-minute products available

Current BoponX use:
- dated NASA GIBS rainfall layer around the farmer-selected field
- described as near-real-time / latest available
- never described as a future forecast

BoponX does not yet derive a quantitative crop rule from IMERG precipitation.

Sources:
https://gpm.nasa.gov/data/directory
https://gpm.nasa.gov/data/imerg

## NASA GIBS / true-color imagery

Current BoponX map can toggle NASA GIBS true-color imagery and the GPM IMERG rainfall layer while preserving OpenStreetMap navigation.

GIBS imagery is visualization of Earth-observation products. It is not itself an agronomic recommendation.

Source:
https://worldview.earthdata.nasa.gov/

## SMAP SPL3SMP_E Version 6

Role:
- candidate regional surface-soil-moisture evidence

Official NSIDC information:
- dataset: SPL3SMP_E
- version: 6
- daily
- 9 km EASE-Grid

Critical 2026 advisory:
NSIDC reports a geolocation issue affecting Standard/NRT products from **14 May to 28 July 2026**. Standard products for that interval are being reprocessed; NRT products will not be replaced.

Current BoponX behavior:
- the source, resolution and warning are visible
- numeric soil-moisture use is QA-gated
- SMAP is never treated as pH or nutrient chemistry

Source:
https://nsidc.org/data/spl3smp_e/versions/6

## NASA POWER recent context

The backend requests:
- T2M
- PRECTOTCORR
- selected farmer coordinates
- a recent 14-day period ending seven days before the request to reduce incomplete-upstream failures
- LST time standard

The response preserves valid-day counts, exact source request URL, provider/source-product metadata, time period, coordinates and limitations.

A precipitation total is suppressed if the requested period is incomplete.

POWER values are regional gridded context, not field measurements and not a weather forecast.

Source:
https://power.larc.nasa.gov/docs/services/api/temporal/daily/

## NASA POWER climatology

The selected planning month also requests a 2001–2020 POWER climatology.

Purpose:
- show historical context alongside recent observations
- avoid treating one historical year as climate evidence

It is not a current-condition measurement or forecast.

Source:
https://power.larc.nasa.gov/docs/services/api/temporal/climatology/

## Real Bangladesh NASA visual case study

The active website uses a real NASA Earth Observatory / USGS Landsat image of **Baniachong, Bangladesh** from the NASA story “Fine-Tuning Irrigation in Asia”.

NASA describes how Landsat thermal information and other satellite data were used in South Asian irrigation research. BoponX presents this as a precedent for connecting Earth observations to farmer decisions; it does not copy the study's irrigation results as BoponX outcomes.

Source:
https://science.nasa.gov/earth/earth-observatory/fine-tuning-irrigation-in-asia-148203/

## Bangladesh crop-calendar evidence

BoponX maintains a calendar-presence index for major crops across official BAMIS regional hubs. This is only a routing layer to relevant evidence.

Current indexed crops:
- Rice Aman
- Rice Aus
- Rice Boro
- Wheat
- Mustard
- Lentil
- Jute
- Maize (Kharif-1)
- Green Gram (Kharif-1)

A crop appearing in the interface means an official BAMIS regional calendar exists. It does not mean the crop has been recommended for the field.

Source:
https://www.bamis.gov.bd/en/calendar

## Farmer-entered evidence

Farmer-known inputs:
- field location
- previous crop
- rain-fed / irrigated / both / unknown
- what happens after heavy rain
- whether a soil-test report exists
- current priority

Numeric pH is accepted only when the farmer explicitly says a soil-test report exists.

Unknown answers remain unknown.

## Decision boundary

The current 90-day routine is decision preparation, not a crop prescription.

The three-season rotation explorer must remain gated until crop requirements, seasonal windows, relevant local soil constraints, crop-sequence constraints, geographic applicability, reuse terms and agronomic review are encoded as deterministic, testable rule packs.
