import { useEffect, useRef, useState } from "react";
import maplibregl, { type Map } from "maplibre-gl";

type Point = { latitude: number; longitude: number };
type LayerId = "base" | "trueColor" | "imerg" | "smap" | "ndvi" | "lst";

type Props = {
  point: Point | null;
  onPick: (point: Point) => void;
  mapDate: string;
};

type LayerSpec = {
  id: LayerId;
  label: string;
  mission: string;
  layer?: string;
  format?: "image/png" | "image/jpeg";
  opacity?: number;
  dateOffset?: number;
};

const LAYERS: LayerSpec[] = [
  { id: "base", label: "Map", mission: "OSM" },
  {
    id: "trueColor",
    label: "True color",
    mission: "MODIS",
    layer: "MODIS_Terra_CorrectedReflectance_TrueColor",
    format: "image/jpeg",
    opacity: 0.94,
  },
  {
    id: "imerg",
    label: "Rain",
    mission: "GPM IMERG",
    layer: "IMERG_Precipitation_Rate_v7_STD",
    format: "image/png",
    opacity: 0.56,
  },
  {
    id: "smap",
    label: "Soil moisture",
    mission: "SMAP",
    layer: "SMAP_L3_Passive_Enhanced_Day_Soil_Moisture",
    format: "image/png",
    opacity: 0.58,
  },
  {
    id: "ndvi",
    label: "Vegetation",
    mission: "MODIS NDVI",
    layer: "MODIS_Terra_NDVI_8Day",
    format: "image/png",
    opacity: 0.62,
  },
  {
    id: "lst",
    label: "Surface heat",
    mission: "MODIS LST",
    layer: "MODIS_Terra_Land_Surface_Temp_Day",
    format: "image/png",
    opacity: 0.58,
  },
];

function isFinitePoint(point: Point) {
  return (
    Number.isFinite(point.latitude) &&
    Number.isFinite(point.longitude) &&
    point.latitude >= -90 &&
    point.latitude <= 90 &&
    point.longitude >= -180 &&
    point.longitude <= 180
  );
}

function wmsUrl(layer: string, format: string, date: string) {
  const bbox = "{bbox-epsg-3857}";
  return (
    "https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi" +
    "?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0" +
    `&LAYERS=${layer}` +
    "&STYLES=" +
    `&FORMAT=${format}` +
    `&TRANSPARENT=${format === "image/png" ? "true" : "false"}` +
    "&HEIGHT=256&WIDTH=256&CRS=EPSG:3857" +
    `&TIME=${date}&BBOX=${bbox}`
  );
}

export default function LocationMap({ point, onPick, mapDate }: Props) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const onPickRef = useRef(onPick);
  const [mapReady, setMapReady] = useState(false);
  const [activeLayer, setActiveLayer] = useState<LayerId>("base");
  const [overlayMessage, setOverlayMessage] = useState("");

  useEffect(() => {
    onPickRef.current = onPick;
  }, [onPick]);

  useEffect(() => {
    const container = rootRef.current;
    if (!container || mapRef.current) return;

    let map: Map | null = null;
    let resizeObserver: ResizeObserver | null = null;

    try {
      map = new maplibregl.Map({
        container,
        center: [15, 15],
        zoom: 1.6,
        minZoom: 1.2,
        maxZoom: 15,
        attributionControl: false,
        renderWorldCopies: false,
        style: {
          version: 8,
          sources: {
            osm: {
              type: "raster",
              tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
              tileSize: 256,
              attribution: "© OpenStreetMap contributors",
            },
          },
          layers: [
            {
              id: "osm",
              type: "raster",
              source: "osm",
              paint: {
                "raster-saturation": -0.55,
                "raster-contrast": 0.12,
                "raster-brightness-max": 0.78,
              },
            },
          ],
        },
      });

      mapRef.current = map;
      map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-right");
      map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

      map.on("click", (event) => {
        const nextPoint = {
          latitude: Number(event.lngLat.lat.toFixed(5)),
          longitude: Number(event.lngLat.lng.toFixed(5)),
        };
        if (isFinitePoint(nextPoint)) onPickRef.current(nextPoint);
      });

      map.on("load", () => {
        setMapReady(true);
        map?.resize();

        for (const spec of LAYERS.filter((item) => item.layer)) {
          try {
            const sourceId = `gibs-${spec.id}`;
            const layerId = `gibs-layer-${spec.id}`;
            if (!map?.getSource(sourceId)) {
              map?.addSource(sourceId, {
                type: "raster",
                tiles: [wmsUrl(spec.layer!, spec.format ?? "image/png", mapDate)],
                tileSize: 256,
                attribution: `NASA GIBS | ${spec.mission}`,
              });
            }
            if (!map?.getLayer(layerId)) {
              map?.addLayer({
                id: layerId,
                type: "raster",
                source: sourceId,
                layout: { visibility: "none" },
                paint: {
                  "raster-opacity": spec.opacity ?? 0.6,
                  "raster-fade-duration": 80,
                },
              });
            }
          } catch {
            setOverlayMessage("One NASA visualization layer could not initialize. Other layers and the field selector remain available.");
          }
        }
      });

      map.on("error", (event) => {
        const message = String(event?.error?.message ?? "").toLowerCase();
        if (message.includes("gibs") || message.includes("raster")) {
          setOverlayMessage("A NASA imagery request failed. Switch layers or continue with the base map. Numeric evidence is loaded separately.");
        }
      });

      resizeObserver = new ResizeObserver(() => {
        window.requestAnimationFrame(() => map?.resize());
      });
      resizeObserver.observe(container);
    } catch {
      setOverlayMessage("The interactive map could not start. You can still choose a field from the 3D Earth or global place search.");
    }

    return () => {
      resizeObserver?.disconnect();
      markerRef.current?.remove();
      markerRef.current = null;
      try {
        map?.remove();
      } catch {
        // Cleanup must never break the app.
      }
      mapRef.current = null;
    };
  }, [mapDate]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !point || !isFinitePoint(point)) return;

    const applyPoint = () => {
      try {
        map.resize();

        if (!markerRef.current) {
          const element = document.createElement("div");
          element.className = "intel-field-pin";
          element.innerHTML =
            '<span class="intel-field-pin-core"></span><span class="intel-field-pin-ring"></span><span class="intel-field-pin-pulse"></span>';
          markerRef.current = new maplibregl.Marker({ element, anchor: "center" }).addTo(map);
        }

        markerRef.current.setLngLat([point.longitude, point.latitude]);

        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        map.easeTo({
          center: [point.longitude, point.latitude],
          zoom: Math.max(map.getZoom(), 7.2),
          bearing: 0,
          pitch: reduceMotion ? 0 : 18,
          duration: reduceMotion ? 0 : 750,
          essential: true,
        });
      } catch {
        setOverlayMessage("The map could not animate to the point, but BoponX kept the selected coordinates.");
      }
    };

    if (map.loaded()) applyPoint();
    else map.once("load", applyPoint);
  }, [point]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    try {
      for (const spec of LAYERS.filter((item) => item.layer)) {
        const layerId = `gibs-layer-${spec.id}`;
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, "visibility", activeLayer === spec.id ? "visible" : "none");
        }
      }

      if (map.getLayer("osm")) {
        map.setPaintProperty("osm", "raster-opacity", activeLayer === "trueColor" ? 0.08 : 0.72);
      }
    } catch {
      setOverlayMessage("That layer could not be switched. The field position and other evidence are still available.");
      setActiveLayer("base");
    }
  }, [activeLayer, mapReady]);

  return (
    <div className="intel-map-shell">
      <div ref={rootRef} className="intel-map" aria-label="Global field and NASA evidence map" />
      <div className="intel-map-grid" aria-hidden="true" />

      <div className="intel-map-layerbar" role="toolbar" aria-label="Earth observation layers">
        {LAYERS.map((layer) => (
          <button
            type="button"
            key={layer.id}
            className={activeLayer === layer.id ? "intel-layer active" : "intel-layer"}
            onClick={() => setActiveLayer(layer.id)}
            disabled={!mapReady && layer.id !== "base"}
            aria-pressed={activeLayer === layer.id}
          >
            <span>{layer.label}</span>
            <small>{layer.mission}</small>
          </button>
        ))}
      </div>

      <div className="intel-map-date">
        <span>Layer date</span>
        <strong>{mapDate}</strong>
      </div>

      <div className="intel-map-help">
        <i />
        Click any point on Earth to move the field
      </div>

      {!mapReady && !overlayMessage && <div className="intel-map-loading">Initializing global map</div>}
      {overlayMessage && <div className="intel-map-warning">{overlayMessage}</div>}
    </div>
  );
}
