# BoponX frontend

The active web client is a full location-first cinematic React/TypeScript experience.

## Stack
- React
- TypeScript
- Vite
- MapLibre GL
- Three.js
- NASA GIBS raster layers
- OpenStreetMap navigation / Nominatim place lookup through the backend

## Active visual flow
1. real NASA Landsat Bangladesh hero + WebGL Earth scene
2. GPS / place search / map-pin field selection
3. NASA true-color + IMERG map
4. recent POWER, POWER climatology and SMAP evidence theatre
5. real NASA Bangladesh irrigation case-study image
6. regional BAMIS crop-calendar evidence
7. farmer-friendly field questions
8. distinct 90-day printable field brief
9. animated three-season rotation target architecture

## Windows

    npm.cmd install
    npm.cmd run build
    npm.cmd run dev

The Vite dev server proxies /api to http://127.0.0.1:8000.

If you were already running an older Vite dev server, stop it with Ctrl+C, run npm.cmd install again because Three.js was added, and restart npm.cmd run dev.

Do not judge the redesign from an old browser tab connected to a stale Vite process. Confirm the project Git SHA and hard-refresh the page.
