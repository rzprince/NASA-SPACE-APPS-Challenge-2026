# Implementation status

**Reviewed:** 28 September 2026

## Implemented

### Global Earth Twin

- interactive globe
- global place search
- browser geolocation
- click anywhere on Earth
- NASA GIBS true color layer
- GPM IMERG layer
- SMAP soil moisture layer
- OpenStreetMap base fallback

### NASA Fusion Engine

- selected point NASA POWER recent request
- T2M
- T2M_MAX
- T2M_MIN
- PRECTOTCORR
- RH2M
- WS2M
- three month POWER climatology
- recent rainfall comparison with historical month
- recent temperature comparison with historical month
- evidence completeness score labelled Decision Readiness

### Local Data Mesh

- verified adapter registry
- Bangladesh deep adapter
- India official agromet reference
- United States official soil and climate references
- Australian official soil and climate references
- UK official agriculture climate reference
- FAO Crop Calendar global fallback
- explicit unsupported country behavior

### Farmer and decision workflow

- crop history
- farmer intended crop
- water source
- drainage observation
- soil test status
- optional report based pH
- farmer priority
- deterministic 90 day plan
- Rotation Lab exploration paths
- evidence gate on final agronomic ranking

### Farmer Action Card

- print layout
- no dependency on clickable links
- source names written as text
- three month actions
- evidence and limitation summary

## Still gated

- automated extraction of every country's agriculture ministry data
- parcel scale soil chemistry
- SMAP numeric decision thresholding
- IMERG numeric crop thresholding
- universal crop requirement database
- universal crop sequence rule database
- final ranked crop rotation recommendation

These items are gated because unsupported completeness would be more damaging than an explicit evidence gap.
