import { Component, useEffect, useMemo, useRef, useState, type ErrorInfo, type MouseEvent, type ReactNode } from "react";
import maplibregl from "maplibre-gl";

type Point = { latitude: number; longitude: number };
export type LayerKey = "trueColor" | "rain" | "soil" | "ndvi" | "temp" | "srtm";

type Props = {
  point: Point | null;
  onPick: (point: Point) => void;
  mapDate: string;
  onMapDateChange?: (date: string) => void;
  activeLayer: LayerKey | null;
  onLayerChange: (layer: LayerKey | null) => void;
};

const NASA_BLUE_MARBLE =
  "https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57730/land_ocean_ice_2048.jpg";

function dateMinusDays(days: number) {
  return new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
}

const TIME_PRESETS = [
  { label: "Latest (-2d)", days: 2 },
  { label: "-14d", days: 14 },
  { label: "-30d", days: 30 },
  { label: "-90d", days: 90 },
  { label: "-180d", days: 180 },
] as const;

function gibsWmsTileUrl(layer: string, date: string, format: "image/png" | "image/jpeg" = "image/png") {
  const transparent = format === "image/png" ? "true" : "false";
  return (
    `https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi?` +
    `SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=${encodeURIComponent(layer)}` +
    `&STYLES=&FORMAT=${encodeURIComponent(format)}&TRANSPARENT=${transparent}` +
    `&CRS=EPSG:3857&WIDTH=256&HEIGHT=256&TIME=${encodeURIComponent(date)}&BBOX={bbox-epsg-3857}`
  );
}

function EarthCanvasFallback({
  point,
  onPick,
}: {
  point: Point | null;
  onPick: (point: Point) => void;
}) {
  const handleSelect = (event: MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const x = Math.min(Math.max(event.clientX - rect.left, 0), rect.width);
    const y = Math.min(Math.max(event.clientY - rect.top, 0), rect.height);
    const longitude = Number(((x / rect.width) * 360 - 180).toFixed(5));
    const latitude = Number((90 - (y / rect.height) * 180).toFixed(5));
    onPick({ latitude, longitude });
  };

  const markerLeft = point ? `${((point.longitude + 180) / 360) * 100}%` : null;
  const markerTop = point ? `${((90 - point.latitude) / 180) * 100}%` : null;

  return (
    <div
      className="earth-fallback-surface"
      onClick={handleSelect}
      role="button"
      tabIndex={0}
      aria-label="2D NASA Earth fallback selector — click anywhere to select field coordinates"
      style={{
        position: "absolute",
        inset: 0,
        cursor: "crosshair",
        backgroundImage: `linear-gradient(rgba(3,9,7,0.22), rgba(3,9,7,0.42)), url(${NASA_BLUE_MARBLE})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      {point && markerLeft && markerTop && (
        <div
          className="earth-field-marker"
          style={{
            position: "absolute",
            left: markerLeft,
            top: markerTop,
            transform: "translate(-50%, -50%)",
            pointerEvents: "none",
          }}
        >
          <span />
          <i />
        </div>
      )}
    </div>
  );
}

class MapErrorBoundary extends Component<
  { point: Point | null; onPick: (point: Point) => void; children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.warn("MapLibre fallback activated:", error, info);
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="earth-globe-stage realistic-earth">
          <EarthCanvasFallback point={this.props.point} onPick={this.props.onPick} />
        </div>
      );
    }
    return this.props.children;
  }
}

function LocationMapInner({
  point,
  onPick,
  mapDate,
  onMapDateChange,
  activeLayer,
  onLayerChange,
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const onPickRef = useRef(onPick);

  const [ready, setReady] = useState(false);
  const [webglFailed, setWebglFailed] = useState(false);
  const [isGlobe, setIsGlobe] = useState(true);
  const [baseStyle, setBaseStyle] = useState<"satellite" | "streets">("satellite");
  const [overlayOpacity, setOverlayOpacity] = useState(0.72);
  const [zoomLevel, setZoomLevel] = useState<number>(6.8);
  const [statusNote, setStatusNote] = useState("3D Globe + High-Resolution Satellite & Village Map Ready");

  const layerConfig = useMemo(
    () => ({
      trueColor: {
        id: "MODIS_Terra_CorrectedReflectance_TrueColor",
        label: "MODIS TRUE COLOR",
        shortLabel: "TRUE COLOR",
        format: "image/jpeg" as const,
        resolution: "250 m",
        detail: "NASA GIBS MODIS Terra daily surface reflectance",
        legendMin: "Clear surface",
        legendMax: "Cloud / Snow",
        gradient: "linear-gradient(90deg, #1b4332, #52b788, #d8f3dc, #ffffff)",
      },
      rain: {
        id: "IMERG_Precipitation_Rate",
        label: "GPM IMERG PRECIPITATION",
        shortLabel: "IMERG RAIN",
        format: "image/png" as const,
        resolution: "0.1° (~10 km)",
        detail: "Near-real-time precipitation rate (mm/hr) — not a forecast",
        legendMin: "0.1 mm/hr",
        legendMax: "50+ mm/hr",
        gradient: "linear-gradient(90deg, #48cae4, #0077b6, #7209b7, #f72585, #ffbe0b)",
      },
      soil: {
        id: "SMAP_L2_Passive_Day_Soil_Moisture_Option2",
        label: "SMAP SURFACE SOIL MOISTURE",
        shortLabel: "SMAP SOIL",
        format: "image/png" as const,
        resolution: "9 km EASE-Grid",
        detail: "Top-5 cm volumetric soil moisture (cm³/cm³) — not pH or NPK",
        legendMin: "0.02 (Dry)",
        legendMax: "0.50+ (Wet)",
        gradient: "linear-gradient(90deg, #d97706, #eab308, #84cc16, #06b6d4, #1d4ed8)",
      },
      ndvi: {
        id: "MODIS_Terra_NDVI_8Day",
        label: "MODIS VEGETATION INDEX (NDVI)",
        shortLabel: "NDVI CANOPY",
        format: "image/png" as const,
        resolution: "250 m (8-day)",
        detail: "Canopy greenness & bare-field detection (-0.2 to 1.0)",
        legendMin: "Bare / Water",
        legendMax: "Dense Crop",
        gradient: "linear-gradient(90deg, #a16207, #eab308, #84cc16, #15803d, #052e16)",
      },
      temp: {
        id: "MODIS_Terra_Land_Surface_Temp_Day",
        label: "MODIS LAND SURFACE TEMP (DAY)",
        shortLabel: "SURFACE HEAT",
        format: "image/png" as const,
        resolution: "1 km",
        detail: "Daytime land surface temperature & evaporative heat stress context",
        legendMin: "10°C",
        legendMax: "45°C+",
        gradient: "linear-gradient(90deg, #38bdf8, #4ade80, #facc15, #f97316, #dc2626)",
      },
      srtm: {
        id: "SRTM_Color_Index",
        label: "NASA SRTM ELEVATION & SLOPE RELIEF",
        shortLabel: "SRTM RELIEF",
        format: "image/png" as const,
        resolution: "30 m / 90 m DEM",
        detail: "Shuttle Radar Topography Mission elevation, drainage basin & slope erosion context",
        legendMin: "Lowland / Haor (0 m)",
        legendMax: "Highland / Terrace",
        gradient: "linear-gradient(90deg, #0ea5e9, #22c55e, #eab308, #d97706, #7c2d12)",
      },
    }),
    [],
  );

  useEffect(() => {
    onPickRef.current = onPick;
  }, [onPick]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || mapRef.current) return;

    let disposed = false;
    let mapInstance: maplibregl.Map | null = null;

    try {
      mapInstance = new maplibregl.Map({
        container,
        attributionControl: false,
        center: [88.6042, 24.3745],
        zoom: 6.8,
        pitch: 18,
        maxZoom: 18,
        minZoom: 1.2,
        style: {
          version: 8,
          sources: {
            satellite: {
              type: "raster",
              tiles: [
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
              ],
              tileSize: 256,
              maxzoom: 18,
            },
            osm: {
              type: "raster",
              tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
              tileSize: 256,
              maxzoom: 19,
            },
            boundaries: {
              type: "raster",
              tiles: [
                "https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
              ],
              tileSize: 256,
              maxzoom: 18,
            },
          },
          layers: [
            {
              id: "satellite-layer",
              type: "raster",
              source: "satellite",
              paint: {
                "raster-opacity": 1,
                "raster-contrast": 0.06,
                "raster-saturation": 0.08,
              },
            },
            {
              id: "osm-layer",
              type: "raster",
              source: "osm",
              layout: { visibility: "none" },
              paint: { "raster-opacity": 1 },
            },
            {
              id: "boundaries-layer",
              type: "raster",
              source: "boundaries",
              paint: { "raster-opacity": 0.88 },
            },
          ],
        },
      });

      mapInstance.on("load", () => {
        if (disposed || !mapInstance) return;
        try {
          if (typeof mapInstance.setProjection === "function") {
            mapInstance.setProjection({ type: "globe" });
          }
        } catch {
          // Keep standard Mercator projection if globe is unsupported on this GPU/version
        }
        setReady(true);
        setWebglFailed(false);
      });

      mapInstance.on("zoom", () => {
        if (disposed || !mapInstance) return;
        try {
          setZoomLevel(Number(mapInstance.getZoom().toFixed(1)));
        } catch {
          // Ignore zoom read errors during teardown
        }
      });

      mapInstance.on("click", (e) => {
        if (disposed || !e?.lngLat) return;
        const lat = Number(e.lngLat.lat.toFixed(5));
        const lon = Number((((e.lngLat.lng + 180) % 360 + 360) % 360 - 180).toFixed(5));
        if (Number.isFinite(lat) && Number.isFinite(lon) && lat >= -90 && lat <= 90) {
          onPickRef.current({ latitude: lat, longitude: lon });
        }
      });

      mapInstance.on("error", () => {
        // Keep base map operational even if an optional overlay tile returns 404
      });

      mapRef.current = mapInstance;
    } catch {
      setReady(false);
      setWebglFailed(true);
      setStatusNote("2D NASA Blue Marble Fallback Active");
    }

    return () => {
      disposed = true;
      try {
        markerRef.current?.remove();
      } catch {
        // Ignore cleanup errors
      }
      markerRef.current = null;
      try {
        mapInstance?.remove();
      } catch {
        // Ignore cleanup errors
      }
      mapRef.current = null;
    };
  }, []);

  // Toggle 3D Globe vs 2D Flat Map
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    try {
      if (typeof map.setProjection === "function") {
        map.setProjection({ type: isGlobe ? "globe" : "mercator" });
      }
    } catch {
      // Older WebGL context fallback
    }
  }, [isGlobe, ready]);

  // Toggle Base Style (Satellite + Place Labels vs OSM Street/Village Map)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    try {
      if (map.getLayer("satellite-layer")) {
        map.setLayoutProperty("satellite-layer", "visibility", baseStyle === "satellite" ? "visible" : "none");
      }
      if (map.getLayer("boundaries-layer")) {
        map.setLayoutProperty("boundaries-layer", "visibility", baseStyle === "satellite" ? "visible" : "none");
      }
      if (map.getLayer("osm-layer")) {
        map.setLayoutProperty("osm-layer", "visibility", baseStyle === "streets" ? "visible" : "none");
      }
    } catch {
      // Ignore layout toggle errors before style ready
    }
  }, [baseStyle, ready]);

  // Manage Live NASA GIBS WMS Overlay Layer
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;

    const sourceId = "nasa-gibs-overlay";
    const layerId = "nasa-gibs-overlay-layer";

    try {
      if (map.getLayer(layerId)) {
        map.removeLayer(layerId);
      }
      if (map.getSource(sourceId)) {
        map.removeSource(sourceId);
      }
    } catch {
      // Ignore removal error if source/layer was not present
    }

    if (!activeLayer) {
      setStatusNote(
        baseStyle === "satellite"
          ? "High-Res Satellite + Place Boundaries Ready"
          : "OpenStreetMap Villages, Upazilas & Rivers Ready",
      );
      return;
    }

    const meta = layerConfig[activeLayer];
    if (!meta) return;
    const tileUrl = gibsWmsTileUrl(meta.id, mapDate, meta.format);

    try {
      map.addSource(sourceId, {
        type: "raster",
        tiles: [tileUrl],
        tileSize: 256,
        maxzoom: 9,
      });
      map.addLayer(
        {
          id: layerId,
          type: "raster",
          source: sourceId,
          paint: {
            "raster-opacity": overlayOpacity,
            "raster-fade-duration": 200,
          },
        },
        map.getLayer("boundaries-layer") ? "boundaries-layer" : undefined,
      );
      setStatusNote(`${meta.label} (${meta.resolution}) · ${mapDate}`);
    } catch {
      setStatusNote(`${meta.label} unavailable for ${mapDate}; base map active`);
    }
  }, [activeLayer, baseStyle, layerConfig, mapDate, overlayOpacity, ready]);

  // Update Field Marker and Smoothly Fly Camera ONLY after map is ready
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !point || !Number.isFinite(point.latitude) || !Number.isFinite(point.longitude)) return;

    try {
      if (!markerRef.current) {
        const el = document.createElement("div");
        el.className = "maplibre-field-pin";
        el.innerHTML = `<span class="pin-core"></span><i class="pin-ring"></i><b class="pin-crosshair"></b>`;
        markerRef.current = new maplibregl.Marker({ element: el, anchor: "center" })
          .setLngLat([point.longitude, point.latitude])
          .addTo(map);
      } else {
        markerRef.current.setLngLat([point.longitude, point.latitude]);
      }

      const currentZoom = map.getZoom();
      const targetZoom = currentZoom < 7.5 ? 10.5 : Math.max(currentZoom, 10.5);
      map.flyTo({
        center: [point.longitude, point.latitude],
        zoom: targetZoom,
        pitch: targetZoom >= 10 ? 28 : 15,
        duration: 1500,
        essential: true,
      });
    } catch {
      // Ignore camera/marker errors if WebGL context is transitioning
    }
  }, [point, ready]);

  function flyToPreset(mode: "space" | "bangladesh" | "field") {
    const map = mapRef.current;
    if (!map || !ready) return;
    try {
      if (mode === "space") {
        map.flyTo({
          center: [point?.longitude ?? 89.25, point?.latitude ?? 23.85],
          zoom: 2.2,
          pitch: 12,
          duration: 1400,
        });
      } else if (mode === "bangladesh") {
        map.flyTo({
          center: [90.35, 23.85],
          zoom: 6.7,
          pitch: 20,
          duration: 1200,
        });
      } else if (point) {
        map.flyTo({
          center: [point.longitude, point.latitude],
          zoom: 14.2,
          pitch: 35,
          duration: 1400,
        });
      }
    } catch {
      // Ignore preset flyTo error
    }
  }

  const currentMeta = activeLayer ? layerConfig[activeLayer] : null;
  const maxSelectableDate = dateMinusDays(1);

  return (
    <div className="earth-globe-stage realistic-earth">
      <div
        ref={containerRef}
        className="earth-globe-map"
        aria-label="Interactive Space-to-Soil 3D Globe and High-Zoom Farm Field Selector"
      />
      {webglFailed && <EarthCanvasFallback point={point} onPick={onPick} />}

      {/* Top-Left HUD: Field Coordinates & Scale */}
      <div className="globe-hud">
        <span className="hud-label">SPACE-TO-SOIL TWIN</span>
        <span>
          {point
            ? `${point.latitude.toFixed(4)}° N, ${point.longitude.toFixed(4)}° E`
            : "Tap anywhere on Earth or zoom to your village"}
        </span>
        <b className="hud-zoom-badge">ZOOM {zoomLevel}x</b>
      </div>

      {/* Top-Right HUD: Projection, Base Map & Zoom Presets */}
      <div className="map-view-toolbar" role="toolbar" aria-label="Map view and zoom controls">
        <div className="toolbar-group">
          <button
            type="button"
            className={isGlobe ? "active" : ""}
            onClick={() => setIsGlobe(true)}
            title="3D Spherical Earth Globe"
          >
            3D Globe
          </button>
          <button
            type="button"
            className={!isGlobe ? "active" : ""}
            onClick={() => setIsGlobe(false)}
            title="2D Flat Agronomic Map"
          >
            2D Map
          </button>
        </div>

        <div className="toolbar-group">
          <button
            type="button"
            className={baseStyle === "satellite" ? "active" : ""}
            onClick={() => setBaseStyle("satellite")}
          >
            Satellite
          </button>
          <button
            type="button"
            className={baseStyle === "streets" ? "active" : ""}
            onClick={() => setBaseStyle("streets")}
          >
            Villages / OSM
          </button>
        </div>

        <div className="toolbar-group">
          <button type="button" onClick={() => flyToPreset("space")} title="Zoom out to Space">
            Space
          </button>
          <button type="button" onClick={() => flyToPreset("bangladesh")} title="Zoom to Bangladesh">
            BD
          </button>
          {point && (
            <button
              type="button"
              className="accent-zoom"
              onClick={() => flyToPreset("field")}
              title="Zoom right down to the selected farm plot"
            >
              Plot 14x
            </button>
          )}
        </div>
      </div>

      {/* NASA GIBS Layer Switcher (6 layers including SRTM Digital Elevation) */}
      <div className="layer-switcher" aria-label="NASA GIBS Earth observation layers">
        {(Object.keys(layerConfig) as LayerKey[]).map((key) => (
          <button
            type="button"
            key={key}
            className={activeLayer === key ? "active" : ""}
            onClick={() => onLayerChange(activeLayer === key ? null : key)}
            disabled={!ready && !webglFailed}
          >
            <i />
            {layerConfig[key].shortLabel}
          </button>
        ))}
      </div>

      {/* NASA Multi-Date Time Scrubber for Seasonal & Bare-Field Inspection */}
      {onMapDateChange && (
        <div className="gibs-time-scrubber" aria-label="NASA GIBS Satellite Date Scrubber">
          <span className="scrubber-label">GIBS DATE:</span>
          {TIME_PRESETS.map((preset) => {
            const target = dateMinusDays(preset.days);
            return (
              <button
                type="button"
                key={preset.label}
                className={mapDate === target ? "active" : ""}
                onClick={() => onMapDateChange(target)}
                title={`View NASA satellite layer on ${target}`}
              >
                {preset.label}
              </button>
            );
          })}
          <input
            type="date"
            value={mapDate}
            max={maxSelectableDate}
            min="2015-01-01"
            onChange={(e) => {
              if (e.target.value) onMapDateChange(e.target.value);
            }}
            aria-label="Custom NASA GIBS observation date"
          />
        </div>
      )}

      {/* Active Layer Legend & Opacity Slider */}
      {currentMeta ? (
        <div className="gibs-legend-card">
          <div className="gibs-legend-head">
            <span>{currentMeta.label}</span>
            <b>{mapDate} · {currentMeta.resolution}</b>
          </div>
          <small>{currentMeta.detail}</small>
          <div className="gibs-gradient-bar" style={{ background: currentMeta.gradient }} />
          <div className="gibs-legend-scale">
            <span>{currentMeta.legendMin}</span>
            <label className="opacity-slider">
              Opacity {Math.round(overlayOpacity * 100)}%
              <input
                type="range"
                min="0.2"
                max="0.95"
                step="0.05"
                value={overlayOpacity}
                onChange={(e) => setOverlayOpacity(Number(e.target.value))}
              />
            </label>
            <span>{currentMeta.legendMax}</span>
          </div>
        </div>
      ) : (
        <div className="globe-date">
          <span>Active Base Layer</span>
          <strong>{statusNote}</strong>
        </div>
      )}
    </div>
  );
}

export default function LocationMap(props: Props) {
  return (
    <MapErrorBoundary point={props.point} onPick={props.onPick}>
      <LocationMapInner {...props} />
    </MapErrorBoundary>
  );
}
