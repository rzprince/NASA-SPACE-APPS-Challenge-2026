import { useEffect, useRef, useState } from "react";
import maplibregl, { type Map } from "maplibre-gl";

type Point = { latitude: number; longitude: number };
type LayerKey = "trueColor" | "rain" | "soil";

type Props = {
  point: Point | null;
  onPick: (point: Point) => void;
  mapDate: string;
  activeLayer: LayerKey | null;
  onLayerChange: (layer: LayerKey | null) => void;
};

function isFinitePoint(point: Point) {
  return Number.isFinite(point.latitude) && Number.isFinite(point.longitude);
}

export default function LocationMap({ point, onPick, mapDate, activeLayer, onLayerChange }: Props) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const onPickRef = useRef(onPick);
  const [ready, setReady] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    onPickRef.current = onPick;
  }, [onPick]);

  useEffect(() => {
    const container = rootRef.current;
    if (!container || mapRef.current) return;

    let map: Map | null = null;
    let observer: ResizeObserver | null = null;

    try {
      map = new maplibregl.Map({
        container,
        center: [30, 18],
        zoom: 1.45,
        minZoom: 1,
        maxZoom: 15,
        attributionControl: false,
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
                "raster-saturation": -0.72,
                "raster-contrast": 0.16,
                "raster-brightness-min": 0.08,
                "raster-brightness-max": 0.48,
              },
            },
          ],
        },
      });

      mapRef.current = map;
      try {
        map.setProjection({ type: "globe" });
      } catch {
        // Older WebGL implementations may fall back to mercator.
      }

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
        setReady(true);
        map?.resize();

        try {
          const bbox = "{bbox-epsg-3857}";
          const sources = {
            trueColor: {
              url:
                "https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi" +
                "?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0" +
                "&LAYERS=MODIS_Terra_CorrectedReflectance_TrueColor" +
                "&STYLES=&FORMAT=image/jpeg&TRANSPARENT=false" +
                "&HEIGHT=256&WIDTH=256&CRS=EPSG:3857" +
                `&TIME=${mapDate}&BBOX=${bbox}`,
              opacity: 0.9,
            },
            rain: {
              url:
                "https://gibs.earthdata.nasa.gov/wms/epsg3857/all/wms.cgi" +
                "?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0" +
                "&LAYERS=IMERG_Precipitation_Rate_v7_STD" +
                "&STYLES=&FORMAT=image/png&TRANSPARENT=true" +
                "&HEIGHT=256&WIDTH=256&CRS=EPSG:3857" +
                `&TIME=${mapDate}&BBOX=${bbox}`,
              opacity: 0.62,
            },
            soil: {
              url:
                "https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi" +
                "?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0" +
                "&LAYERS=SMAP_L2_Passive_Day_Soil_Moisture_Option2" +
                "&STYLES=&FORMAT=image/png&TRANSPARENT=true" +
                "&HEIGHT=256&WIDTH=256&CRS=EPSG:3857" +
                `&TIME=${mapDate}&BBOX=${bbox}`,
              opacity: 0.72,
            },
          } as const;

          Object.entries(sources).forEach(([key, config]) => {
            const sourceId = `nasa-${key}`;
            if (!map?.getSource(sourceId)) {
              map?.addSource(sourceId, {
                type: "raster",
                tiles: [config.url],
                tileSize: 256,
                attribution: "NASA GIBS",
              });
            }
            if (!map?.getLayer(sourceId)) {
              map?.addLayer({
                id: sourceId,
                type: "raster",
                source: sourceId,
                layout: { visibility: "none" },
                paint: { "raster-opacity": config.opacity, "raster-fade-duration": 80 },
              });
            }
          });
        } catch {
          setMessage("NASA spatial layers are unavailable. Field selection and POWER analysis still work.");
        }
      });

      map.on("error", (event) => {
        const error = String(event?.error?.message ?? "");
        if (/gibs|NASA|IMERG|SMAP/i.test(error)) {
          setMessage("One NASA layer could not load. Switch layers or continue with the field analysis.");
        }
      });

      observer = new ResizeObserver(() => requestAnimationFrame(() => map?.resize()));
      observer.observe(container);
    } catch {
      setMessage("The 3D Earth view could not start. Use place search or location access to continue.");
    }

    return () => {
      observer?.disconnect();
      markerRef.current?.remove();
      try {
        map?.remove();
      } catch {
        // Cleanup should never crash the application.
      }
      mapRef.current = null;
    };
  }, [mapDate]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;

    const layerIds = ["trueColor", "rain", "soil"] as const;
    try {
      layerIds.forEach((key) => {
        const id = `nasa-${key}`;
        if (map.getLayer(id)) {
          map.setLayoutProperty(id, "visibility", activeLayer === key ? "visible" : "none");
        }
      });
      if (map.getLayer("osm")) {
        map.setLayoutProperty("osm", "visibility", activeLayer === "trueColor" ? "none" : "visible");
      }
    } catch {
      setMessage("The selected Earth layer could not be displayed.");
    }
  }, [activeLayer, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !point || !isFinitePoint(point)) return;

    const apply = () => {
      try {
        map.resize();
        if (!markerRef.current) {
          const element = document.createElement("div");
          element.className = "earth-field-marker";
          element.innerHTML = '<span></span><i></i>';
          markerRef.current = new maplibregl.Marker({ element, anchor: "center" }).addTo(map);
        }
        markerRef.current.setLngLat([point.longitude, point.latitude]);
        map.easeTo({
          center: [point.longitude, point.latitude],
          zoom: Math.max(map.getZoom(), 7.6),
          duration: 950,
          essential: true,
        });
      } catch {
        setMessage("The field is selected, but the camera could not animate to it.");
      }
    };

    if (map.loaded()) apply();
    else map.once("load", apply);
  }, [point]);

  return (
    <div className="earth-globe-stage">
      <div ref={rootRef} className="earth-globe-map" aria-label="Interactive global Earth field selector" />
      <div className="globe-hud">
        <span className="hud-label">EARTH TWIN</span>
        <span>{point ? `${point.latitude.toFixed(4)}°, ${point.longitude.toFixed(4)}°` : "Tap the globe to select a field"}</span>
      </div>
      <div className="layer-switcher" aria-label="NASA spatial layers">
        {[
          ["trueColor", "TRUE COLOR"],
          ["rain", "IMERG RAIN"],
          ["soil", "SMAP SOIL"],
        ].map(([key, label]) => (
          <button
            type="button"
            key={key}
            className={activeLayer === key ? "active" : ""}
            onClick={() => onLayerChange(activeLayer === key ? null : key as LayerKey)}
            disabled={!ready}
          >
            <i />
            {label}
          </button>
        ))}
      </div>
      <div className="globe-date">NASA layer date <strong>{mapDate}</strong></div>
      {message && <div className="globe-message">{message}</div>}
    </div>
  );
}
