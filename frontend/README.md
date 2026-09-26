# BoponX frontend

The active frontend is a location-first React + TypeScript interface using MapLibre.

Core screens:
- field location by browser GPS, region search, or map pin
- location-specific evidence states
- dated NASA GIBS IMERG rainfall layer
- NASA POWER selected-point context
- farmer-friendly questions with conditional soil-test details
- distinct 90-day field brief
- printable bilingual report
- locked rotation explorer until agronomic rules pass review

Windows commands:

    npm.cmd install
    npm.cmd run build
    npm.cmd run dev

The Vite dev server proxies /api to http://127.0.0.1:8000.

Manual checks should cover GPS allowed/denied, at least three Bangladesh locations, Bangla mode, 360 px layout, reduced motion, and Print / Save PDF.
