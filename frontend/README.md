# BoponX frontend

The active client is an English only, location aware, cinematic React and TypeScript experience.

## Stack

- React
- TypeScript
- Vite
- MapLibre GL
- Three.js
- NASA GIBS raster layers
- OpenStreetMap navigation
- Nominatim place lookup through the backend

## Active visual flow

1. real NASA Landsat Bangladesh hero with WebGL Earth
2. browser location, place search or map point selection
3. OpenStreetMap base with optional NASA true color and IMERG layers
4. recent NASA POWER, climatology and SMAP evidence cards
5. real NASA Bangladesh irrigation case study image
6. regional BAMIS crop calendar evidence
7. farmer questions with professional SVG icons
8. distinct 90 day printable field brief
9. animated three season rotation architecture

## Stability safeguards

- off screen Three.js scenes pause rendering
- map movement is guarded so a failed animation does not crash React
- NASA map overlays are optional and cannot remove the base map
- field coordinates are validated before use
- 90 day plan generation does not repeat NASA network calls
- report rendering guards missing external data
- the root React tree has an error boundary so unexpected exceptions do not produce a blank screen

## Windows

    npm.cmd install
    npm.cmd run build
    npm.cmd run dev

The Vite development server proxies /api to http://127.0.0.1:8000.

If you downloaded a new ZIP, run npm.cmd install again before starting Vite.

If you were already running an older frontend, stop it with Ctrl+C and restart it. Then use Ctrl+Shift+R in the browser.
