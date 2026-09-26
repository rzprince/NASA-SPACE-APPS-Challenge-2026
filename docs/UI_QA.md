# BoponX UI / field-workflow QA

## Location
- [ ] “Use my location” asks permission only after the button is pressed.
- [ ] Denying GPS leaves search and map selection fully usable.
- [ ] Search can select several different Bangladesh regions.
- [ ] Tapping the map moves the farm marker.
- [ ] Moving location changes the resolved regional context.
- [ ] Exact coordinates are not written to localStorage, cookies, or backend persistence.
- [ ] Map date and NASA GIBS/IMERG label remain visible.
- [ ] Unsupported/outside-Bangladesh locations fail clearly.

## Farmer questions
- [ ] No numeric pH appears unless “soil-test report: yes” is selected.
- [ ] Backend rejects pH without a soil report.
- [ ] Unknown/not-sure answers are accepted.
- [ ] Questions use plain English/Bangla.
- [ ] Bangla is readable at normal phone viewing distance.

## 90-day report
- [ ] Month 1, 2, and 3 have visibly different objectives.
- [ ] No repeated generic checklist is presented as intelligence.
- [ ] No crop, sowing date, fertilizer amount, yield gain, or water-saving percentage is invented.
- [ ] NASA/local sources are visible.
- [ ] Historical/recent labels cannot be confused with forecasts.
- [ ] Print/Save PDF is legible in English and Bangla.

## Visual quality
- [ ] 360 px phone has no clipped controls.
- [ ] Samsung/Android map gestures are usable.
- [ ] Desktop layout does not feel like a generic dashboard template.
- [ ] Motion responds to data/user actions.
- [ ] prefers-reduced-motion preserves the workflow.
- [ ] Keyboard focus is visible.
- [ ] Core workflow remains understandable if map tiles fail.

## Data failure
- [ ] NASA POWER live query failure shows unavailable with no replacement number.
- [ ] GIBS layer failure does not block location selection.
- [ ] Any cached data shows its timestamp and cache state.
