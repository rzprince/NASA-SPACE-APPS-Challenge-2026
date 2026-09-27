# BoponX demo QA

## Opening

- [ ] NASA Bangladesh image loads
- [ ] Three.js Earth renders
- [ ] hero text fits the presentation screen
- [ ] no release label appears
- [ ] all farmer facing text is English
- [ ] no floating card blocks important hero copy

## Field location

- [ ] Allow location permission
- [ ] marker moves to the returned coordinates
- [ ] page remains visible after the location update
- [ ] deny location permission and confirm search still works
- [ ] search a village or district and choose a result
- [ ] click directly on the map and confirm the marker moves
- [ ] field label and coordinates update
- [ ] OpenStreetMap remains visible if NASA imagery fails
- [ ] NASA true color can be switched on and off
- [ ] IMERG rain can be switched on and off
- [ ] map failure messages are visible instead of a blank area

## NASA evidence

- [ ] selected field changes the regional context
- [ ] recent POWER either shows real values or a clear unavailable state
- [ ] climatology either shows real values or a clear unavailable state
- [ ] IMERG remains labelled as recent rainfall evidence and not forecast
- [ ] SMAP remains labelled as regional soil moisture and never pH
- [ ] 2026 SMAP quality note remains visible

## Local evidence

- [ ] selected region name changes after a new field is chosen
- [ ] BAMIS calendar source count updates
- [ ] calendar links open the source
- [ ] interface does not call a calendar a crop recommendation

## Farmer questions

- [ ] every crop option shows a recognisable icon
- [ ] water choices show icons with no text overlap
- [ ] heavy rain choices show icons with no text overlap
- [ ] soil test choices show icons
- [ ] farmer priority choices show icons
- [ ] Not sure works in every relevant section
- [ ] pH is hidden unless soil test report is Yes
- [ ] backend rejects pH without a declared soil test

## 90 day brief

- [ ] Build my 90 day field brief completes without a blank screen
- [ ] Month 1 is Know the field
- [ ] Month 2 is Watch the change
- [ ] Month 3 is Decide the next move
- [ ] the three task sets are different
- [ ] changing priority changes the Month 2 priority task
- [ ] loaded NASA context appears when available
- [ ] unavailable NASA data does not crash the report
- [ ] Print or Save PDF opens a readable print view

## Recovery and performance

- [ ] scrolling through the whole page never produces an empty dark viewport
- [ ] off screen Earth scenes stop continuous rendering
- [ ] unexpected React errors show the recovery screen rather than a blank page
- [ ] reduced motion mode keeps the workflow usable
- [ ] 360 px mobile layout has no clipped controls
- [ ] Samsung browser map gestures work

## Failure rehearsal

- [ ] backend stopped
- [ ] NASA POWER unavailable
- [ ] geocoder unavailable
- [ ] NASA GIBS unavailable
- [ ] GPS denied
- [ ] slow network
