# BoponX data source register

**Reviewed:** 28 September 2026

BoponX separates spatial Earth observation, agroclimate context, local agriculture evidence and farmer supplied observations. A source is used only for the role its documentation supports.

| Source | Product role in BoponX | Current implementation | Decision boundary |
| --- | --- | --- | --- |
| NASA Blue Marble | complete global visual Earth reference | static NASA 2048 × 1024 texture loaded first for the 3D Earth | reference imagery, not current conditions |
| MODIS Terra Corrected Reflectance True Color through NASA GIBS | dated true color spatial overlay | optional globe overlay with dark no data pixels masked so the complete Earth remains visible | visual context, not a crop recommendation |
| GPM IMERG | recent precipitation spatial evidence | optional NASA GIBS precipitation overlay | not a future forecast or field rain gauge |
| SMAP | regional surface soil moisture context | optional spatial overlay; numeric crop thresholding remains gated | not pH, nutrients or parcel chemistry |
| NASA POWER Daily | recent agroclimate context | selected coordinate query for temperature, precipitation, humidity and wind | gridded regional context, not a field sensor |
| NASA POWER Climatology | historical planning reference | three consecutive monthly references for the selected coordinates | historical context, not a forecast |
| NASA GIBS Reference Labels | geographic orientation on the globe | transparent reference label sphere that becomes more visible when zoomed closer | map reference only |
| BAMIS | Bangladesh agromet and crop weather evidence | regional crop calendar evidence and official source routing | source presence does not automatically prove crop suitability |
| BARC Crop Zoning | Bangladesh crop zoning and suitability reference | official source routing and decision evidence register | use remains subject to crop, location and source interpretation |
| Agriculture Information Service | Bangladesh crop production and farmer information | official source routing and printed farmer support context | government guidance remains separate from NASA measurements |
| Farmer observations | crop history, intention, water, drainage, soil test and priority | direct input to deterministic planning logic | unknown remains unknown |

## NASA Blue Marble

The base Earth texture comes from NASA Visible Earth / Earth Observatory and is a complete global equirectangular reference image. It is loaded before dated overlays to keep the Earth selectable even if a live imagery service is unavailable.

## NASA GIBS overlays

BoponX requests dated global WMS imagery for optional Earth observation layers. The application never removes the complete Blue Marble base when an overlay fails.

The GIBS reference label layer is loaded independently to provide geographic names on the globe.

## NASA POWER

Recent POWER requests use the selected latitude and longitude. The current workflow requests:

- T2M
- T2M_MAX
- T2M_MIN
- PRECTOTCORR
- RH2M
- WS2M

The climatology workflow requests the planning month and next two calendar months for the same selected point.

Missing upstream data remain unavailable rather than being replaced by sample values.

## Bangladesh agriculture evidence

The Bangladesh source mesh connects:

- Ministry of Agriculture
- Department of Agricultural Extension
- Agriculture Information Service
- Bangladesh Agro Meteorological Information Service
- Bangladesh Agricultural Research Council Crop Zoning
- FAO Crop Calendar

BARC states that its crop zoning work uses agro edaphic and agro climatic suitability information and provides upazila wise crop zoning reference. AIS provides crop production technologies and seasonal agriculture information. BAMIS provides crop weather calendar and agrometeorological information.

## National agriculture adapters

A national government link is labelled official only after review.

The current reviewed registry contains adapters for Bangladesh, India, United States, Canada, Japan, Brazil, Philippines, Sri Lanka, Australia and United Kingdom.

Countries without a reviewed adapter continue to receive NASA analysis and FAO references, plus a clearly labelled discovery route to the national agriculture authority.

## Scientific rule

No generative model performs the climate calculations or supplies missing soil chemistry.

The deterministic decision layer must preserve:

- dataset identity
- selected coordinates
- period or layer date
- historical versus recent meaning
- source role
- known limitations
