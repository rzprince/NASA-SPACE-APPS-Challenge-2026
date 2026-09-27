# BoponX visual / workflow QA

## Opening experience
- [ ] Real NASA Bangladesh Landsat image loads.
- [ ] Three.js Earth scene renders without console errors.
- [ ] Opening remains readable if WebGL is unavailable or motion is reduced.
- [ ] No release/version label appears anywhere in farmer-facing UI.
- [ ] Real-image credit remains visible.
- [ ] Hero CTA reaches location flow.

## Location
- [ ] Already-granted browser geolocation can populate the map automatically.
- [ ] Otherwise, geolocation is requested only after the farmer taps a location control.
- [ ] Denying GPS leaves search and map selection usable.
- [ ] Search can find village/upazila/district/place results.
- [ ] Regional fallback still works if geocoder is unavailable.
- [ ] Tapping map moves the field pin.
- [ ] Map zoom/tilt follows the new field.
- [ ] NASA true-color layer toggles.
- [ ] IMERG rainfall layer toggles.
- [ ] Changing field changes POWER/context/calendar evidence.
- [ ] Exact coordinates are not persisted by default.

## NASA evidence
- [ ] GPM IMERG card says near-real-time, not forecast.
- [ ] IMERG date and 0.1°/~10 km context remain visible.
- [ ] POWER recent values show their observation period.
- [ ] POWER failure shows unavailable instead of sample data.
- [ ] Climatology shows historical-baseline wording.
- [ ] SMAP is explicitly regional soil moisture, never pH.
- [ ] 14 May–28 July 2026 SMAP advisory is visible.

## Farmer flow
- [ ] Form stays locked until a Bangladesh field point exists.
- [ ] Previous crop supports Not sure.
- [ ] Water source supports Not sure.
- [ ] Drainage/waterlogging observation supports Not sure.
- [ ] pH field is hidden unless soil-test report = Yes.
- [ ] Backend rejects pH without explicit soil-test state.
- [ ] Water/soil/stability priority changes Month 2 routine.

## 90-day brief
- [ ] Month 1, 2 and 3 have visibly different objectives and task sets.
- [ ] Recent evidence and historical baseline are visually separated.
- [ ] BAMIS crop links are labelled source evidence, not recommendations.
- [ ] No crop sequence / planting date / yield claim is fabricated.
- [ ] Print / Save PDF remains readable in Bangla and English.

## Mobile / accessibility
- [ ] 360 px layout has no clipped controls.
- [ ] Samsung browser map gestures work.
- [ ] Bangla line-height is comfortable.
- [ ] keyboard focus is visible.
- [ ] prefers-reduced-motion removes continuous motion but keeps the full workflow.
- [ ] browser zoom at 200% remains usable.

## Failure rehearsal
- [ ] backend stopped
- [ ] NASA POWER unavailable
- [ ] geocoder unavailable
- [ ] NASA GIBS imagery unavailable
- [ ] GPS denied
- [ ] slow network


## Regression checks added after screenshot review

- [ ] Hero text fits a 1366 by 768 laptop viewport without clipping.
- [ ] Hero text fits a 1920 by 1080 desktop viewport without extending below the first screen.
- [ ] All farmer facing copy is English.
- [ ] No farmer facing sentence uses a hyphen character.
- [ ] Scrolling from hero to the location section never produces an empty dark viewport.
- [ ] Scrolling further down never leaves reveal sections invisible.
- [ ] Base map remains visible even if NASA GIBS imagery fails.
- [ ] Location permission allowed updates the map marker and selected coordinates.
- [ ] Location permission denied leaves place search and map pin fully usable.
- [ ] Selecting a search result updates the marker, recent POWER request and regional crop evidence.
- [ ] Farmer questions remain selectable before location is chosen.
- [ ] Plan generation gives a clear location message when no field point exists.
