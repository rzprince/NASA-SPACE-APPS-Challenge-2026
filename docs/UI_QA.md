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
