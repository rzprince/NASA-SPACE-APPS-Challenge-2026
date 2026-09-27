import { useEffect, useRef, useState } from "react";
import maplibregl, { type Map } from "maplibre-gl";

type Point = { latitude: number; longitude: number };

type Props = {
  point: Point | null;
  onPick: (point: Point) => void;
  mapDate: string;
};

function isFinitePoint(point: Point) {
  return Number.isFinite(point.latitude) && Number.isFinite(point.longitude);
}

export default function LocationMap({ point, onPick, mapDate }: Props) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const onPickRef = useRef(onPick);
  const [mapReady, setMapReady] = useState(false);
  const [rainVisible, setRainVisible] = useState(false);
  const [imageryVisible, setImageryVisible] = useState(false);
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
        center: [90.35, 23.75],
        zoom: 5.45,
        minZoom: 4.5,
        maxZoom: 15,
        maxBounds: [[87.4, 19.8], [93.4, 27.3]],
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
          layers: [{ id: "osm", type: "raster", source: "osm" }],
        },
      });

      mapRef.current = map;
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
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

        try {
          const bbox = "{bbox-epsg-3857}";
          const trueColorUrl =
            "https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi" +
            "?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0" +
            "&LAYERS=MODIS_Terra_CorrectedReflectance_TrueColor" +
            "&STYLES=&FORMAT=image/jpeg&TRANSPARENT=false" +
            "&HEIGHT=256&WIDTH=256&CRS=EPSG:3857" +
            `&TIME=${mapDate}&BBOX=${bbox}`;

          const rainUrl =
            "https://gibs.earthdata.nasa.gov/wms/epsg3857/all/wms.cgi" +
            "?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0" +
            "&LAYERS=IMERG_Precipitation_Rate_v7_STD" +
            "&STYLES=&FORMAT=image/png&TRANSPARENT=true" +
            "&HEIGHT=256&WIDTH=256&CRS=EPSG:3857" +
            `&TIME=${mapDate}&BBOX=${bbox}`;

          if (!map?.getSource("nasaTrueColor")) {
            map?.addSource("nasaTrueColor", {
              type: "raster",
              tiles: [trueColorUrl],
              tileSize: 256,
              attribution: "NASA GIBS",
            });
          }

          if (!map?.getLayer("nasaTrueColor")) {
            map?.addLayer({
              id: "nasaTrueColor",
              type: "raster",
              source: "nasaTrueColor",
              layout: { visibility: "none" },
              paint: { "raster-opacity": 0.88, "raster-fade-duration": 80 },
            });
          }

          if (!map?.getSource("nasaRain")) {
            map?.addSource("nasaRain", {
              type: "raster",
              tiles: [rainUrl],
              tileSize: 256,
              attribution: "NASA GIBS and GPM IMERG",
            });
          }

          if (!map?.getLayer("nasaRain")) {
            map?.addLayer({
              id: "nasaRain",
              type: "raster",
              source: "nasaRain",
              layout: { visibility: "none" },
              paint: { "raster-opacity": 0.5, "raster-fade-duration": 80 },
            });
          }
        } catch {
          setOverlayMessage("NASA map imagery is unavailable right now. The field map and location workflow still work.");
        }
      });

      map.on("error", (event) => {
        const message = String(event?.error?.message ?? "");
        if (message.includes("gibs") || message.includes("NASA") || message.includes("IMERG")) {
          setOverlayMessage("A NASA map layer could not load. You can still choose the field and use the rest of BoponX.");
        }
      });

      resizeObserver = new ResizeObserver(() => {
        window.requestAnimationFrame(() => map?.resize());
      });
      resizeObserver.observe(container);
    } catch {
      setOverlayMessage("The interactive map could not start. Search for a place to continue.");
    }

    return () => {
      resizeObserver?.disconnect();
      markerRef.current?.remove();
      markerRef.current = null;
      try {
        map?.remove();
      } catch {
        // Map cleanup must never break the application.
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
          element.className = "field-pin";
          element.innerHTML = '<span class="field-pin-core"></span><span class="field-pin-ring"></span>';
          markerRef.current = new maplibregl.Marker({ element, anchor: "center" }).addTo(map);
        }

        markerRef.current.setLngLat([point.longitude, point.latitude]);

        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        map.easeTo({
          center: [point.longitude, point.latitude],
          zoom: Math.max(map.getZoom(), 9),
          bearing: 0,
          duration: reduceMotion ? 0 : 650,
          essential: true,
        });
      } catch {
        setOverlayMessage("The map could not animate to that point. The selected coordinates are still saved for this session.");
      }
    };

    if (map.loaded()) applyPoint();
    else map.once("load", applyPoint);
  }, [point]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    try {
      if (map.getLayer("nasaRain")) {
        map.setLayoutProperty("nasaRain", "visibility", rainVisible ? "visible" : "none");
      }
      if (map.getLayer("nasaTrueColor")) {
        map.setLayoutProperty("nasaTrueColor", "visibility", imageryVisible ? "visible" : "none");
      }
      if (map.getLayer("osm")) {
        map.setLayoutProperty("osm", "visibility", imageryVisible ? "none" : "visible");
      }
    } catch {
      setOverlayMessage("The NASA overlay could not be switched. The standard map remains available.");
      setImageryVisible(false);
      setRainVisible(false);
    }
  }, [rainVisible, imageryVisible, mapReady]);

  return (
    <div className="map-stage">
      <div ref={rootRef} className="field-map" aria-label="Interactive Bangladesh farm map" />
      <div className="map-vignette" aria-hidden="true" />

      <div className="map-toolbar">
        <button
          type="button"
          className={imageryVisible ? "map-chip active" : "map-chip"}
          onClick={() => setImageryVisible((value) => !value)}
          aria-pressed={imageryVisible}
          disabled={!mapReady}
        >
          <span className="chip-orb imagery" />
          NASA true color
        </button>

        <button
          type="button"
          className={rainVisible ? "map-chip active" : "map-chip"}
          onClick={() => setRainVisible((value) => !value)}
          aria-pressed={rainVisible}
          disabled={!mapReady}
        >
          <span className="chip-orb rain" />
          IMERG rain
        </button>
      </div>

      <div className="map-date">
        <span>NASA layer date</span>
        <strong>{mapDate}</strong>
      </div>

      <div className="map-help">
        <span className="map-help-dot" />
        Choose any point in Bangladesh to set the field location
      </div>

      {!mapReady && !overlayMessage && <div className="map-loading-note">Loading the field map…</div>}
      {overlayMessage && <div className="map-overlay-note">{overlayMessage}</div>}
    </div>
  );
}
