# Evidence register

**Reviewed:** 28 September 2026

## Challenge

Field Shift asks for a decision support tool using NASA Earth observations with local soil information, crop characteristics and farmer priorities to explore crop rotation strategies.

Source:
https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/

## GPM IMERG Early V07B

Role:
recent precipitation spatial context

NASA documentation currently lists:

- current algorithm V07B
- January 1998 to present
- about 4 hour minimum latency
- 0.1 degree / about 10 km
- 30 minute products available

BoponX uses IMERG as a spatial evidence layer.

It is not presented as a forecast or field rain gauge.

Source:
https://gpm.nasa.gov/data/directory

## SMAP SPL3SMP_E Version 6

Role:
regional surface soil moisture context

Official product characteristics:

- SPL3SMP_E
- Version 6
- daily
- 9 km EASE-Grid

2026 advisory:

NSIDC reports a geolocation issue affecting Standard and Near Real Time products from 14 May to 28 July 2026. Standard products are being reprocessed. Near Real Time products will not be replaced.

BoponX keeps numeric use gated and exposes the spatial layer as regional context.

Source:
https://nsidc.org/data/spl3smp_e/versions/6

## NASA POWER Daily

Role:
selected point recent agroclimate context

Requested variables:

- T2M
- T2M_MAX
- T2M_MIN
- PRECTOTCORR
- RH2M
- WS2M

The request ends several days before today to reduce incomplete upstream values.

POWER is gridded context, not an instrument in the farmer's field.

Source:
https://power.larc.nasa.gov/docs/services/api/temporal/daily/

## NASA POWER climatology

Role:
historical monthly comparison

BoponX requests three consecutive calendar months for the selected location and compares recent rainfall and temperature with the first planning month historical reference.

These values are context, not a forecast.

Source:
https://power.larc.nasa.gov/docs/services/api/temporal/climatology/

## NASA GIBS

Role:
delivery of Earth imagery and product visualization in the global Earth Twin

Source:
https://worldview.earthdata.nasa.gov/

## FAO Crop Calendar

Role:
global crop calendar reference when a verified national adapter is not available

FAO describes the Crop Calendar as a searchable platform for crop production planning by country, crop and agroecological zone.

Source:
https://cropcalendar.apps.fao.org/

## Verified public sector adapters

### Bangladesh

BAMIS / Department of Agricultural Extension  
https://www.bamis.gov.bd/

BARC Crop Zoning  
https://apps.barc.gov.bd/cropzoning/

### India

India Meteorological Department Agromet Advisory Services  
https://mausam.imd.gov.in/responsive/agromet_adv_ser_district_current_en.php

### United States

USDA Web Soil Survey  
https://websoilsurvey.sc.egov.usda.gov/App/

USDA Climate Hubs  
https://www.climatehubs.usda.gov/commodity/crops

### Australia

Department of Agriculture, Fisheries and Forestry soil information  
https://www.agriculture.gov.au/agriculture-land/farm-food-drought/natural-resources/soils

Agriculture climate adaptation information  
https://www.agriculture.gov.au/agriculture-land/farm-food-drought/climatechange

### United Kingdom

DEFRA agriculture and climate change collection  
https://www.gov.uk/government/collections/agricultural-statistics-and-climate-change

## Boundary

The presence of an official source does not mean BoponX has already encoded every agronomic rule from that source.

Global NASA coverage is implemented.

Country specific agronomic rule packs remain a reviewed adapter process.
