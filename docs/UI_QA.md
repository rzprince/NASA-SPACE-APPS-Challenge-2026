# Earth Command QA checklist

## Global location

- [ ] search Dhaka
- [ ] search Delhi
- [ ] search Iowa
- [ ] search London
- [ ] click a point directly on the globe
- [ ] allow browser location
- [ ] deny browser location and continue with search
- [ ] selected marker follows the field

## NASA layers

- [ ] true color toggles
- [ ] IMERG toggles
- [ ] SMAP toggles
- [ ] standard map remains usable when a NASA layer fails
- [ ] NASA layer date is visible
- [ ] IMERG is never described as forecast
- [ ] SMAP is never described as pH

## NASA POWER

- [ ] recent temperature loads
- [ ] max temperature loads
- [ ] precipitation loads
- [ ] humidity loads
- [ ] wind loads
- [ ] three month climatology loads
- [ ] unavailable state never fabricates values

## Local Data Mesh

- [ ] Bangladesh shows BAMIS and BARC
- [ ] India shows IMD Agromet
- [ ] United States shows USDA sources
- [ ] unreviewed country shows global fallback only
- [ ] no unsupported country is labelled as having a verified government adapter

## Rotation Lab

- [ ] crop history supports several crops
- [ ] farmer intention can be selected
- [ ] water and drainage inputs work
- [ ] soil test and pH logic works
- [ ] priority works
- [ ] exploration paths render
- [ ] paths are labelled as exploration, not ranked prescriptions
- [ ] decision engine produces 90 day plan

## Farmer Action Card

- [ ] no clickable link is required to understand the printout
- [ ] field name and coordinates print
- [ ] decision message prints
- [ ] three month plan prints
- [ ] evidence source names print
- [ ] scientific limitation prints
- [ ] A4 landscape remains readable

## Performance

- [ ] globe works on presentation laptop
- [ ] mobile layout remains usable
- [ ] no blank screen after GPS
- [ ] no blank screen after plan generation
- [ ] app recovery screen appears on unexpected React error


## Realistic Earth regression checks

- [ ] Earth renders as a spherical planet against space, not as a flat map
- [ ] NASA Blue Marble or dated true color imagery loads
- [ ] drag rotates the planet
- [ ] mouse wheel or trackpad zoom changes camera distance
- [ ] tapping Bangladesh selects a Bangladesh coordinate
- [ ] tapping another continent returns plausible global coordinates
- [ ] browser geolocation moves the camera to the selected field
- [ ] place search moves the field marker and camera
- [ ] IMERG overlay appears on top of the Earth texture
- [ ] SMAP overlay appears on top of the Earth texture
- [ ] overlay failure leaves the base Earth selectable
- [ ] selected country shows verified government links when an adapter exists
- [ ] every country shows the government portal finder
- [ ] portal finder is never labelled verified
- [ ] FAO global references remain visible


## Globe and location recovery regression (October 2026)

- [ ] WebGL2 available: textured 3D globe loads and click selection matches actual country/coordinate (test Greenwich, Bangladesh and the Americas)
- [ ] WebGL2 disabled: projected 2D globe displays, rotates by drag, zooms by wheel, accepts clicks and keyboard Enter
- [ ] WebGL initialization failure logs the actual technical exception in developer console (without a blank map)
- [ ] 2D NASA image host unavailable: coordinate-selectable untextured globe remains, with honest source status
- [ ] selecting field via search/GPS/manual coordinates updates field marker immediately, including after fallback activation
- [ ] test with GPS permission allowed on HTTPS or desktop localhost
- [ ] test with GPS permission denied and device location switched off: clear local error appears below button
- [ ] test on mobile http://192.168.x.x: explicit HTTPS-required message appears rather than misleading permission error
- [ ] manually enter valid coordinates "23.8103, 90.4125" when GPS is unavailable; invalid ranges are rejected
- [ ] optional IMERG/SMAP/true-color layers are disabled and identified as unavailable in 2D compatibility mode
- [ ] switch between Earth Twin/Rotation Lab and back, without stale canvas, RAF loops or lost pointer interactions

Note: secure-context geolocation is a browser security rule. On mobile LAN HTTP,
no JavaScript change can enable GPS. Test on HTTPS deployment for actual phone
geolocation. Use an HTTPS origin and grant location permission. Desktop
http://localhost is generally exempted by browsers.
