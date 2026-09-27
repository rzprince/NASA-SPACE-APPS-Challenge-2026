import { useEffect, useRef, useState } from "react";
import maplibregl, { type Map } from "maplibre-gl";

type Point = { latitude: number; longitude: number };

type Props = {
  point: Point | null;
  onPick: (point: Point) => void;
  mapDate: string;
};

export default function LocationMap({ point, onPick, mapDate }: Props) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const onPickRef = useRef(onPick);
  const [rainVisible, setRainVisible] = useState(true);
  const [imageryVisible, setImageryVisible] = useState(false);
  const [overlayMessage, setOverlayMessage] = useState("");

  useEffect(() => {
    onPickRef.current = onPick;
  }, [onPick]);

  useEffect(() => {
    if (!rootRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: rootRef.current,
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

    map.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), "top-right");
    map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: "NASA GIBS" }), "bottom-right");

    const handleClick = (event: maplibregl.MapMouseEvent) => {
      onPickRef.current({
        latitude: Number(event.lngLat.lat.toFixed(5)),
        longitude: Number(event.lngLat.lng.toFixed(5)),
      });
    };

    map.on("click", handleClick);

    map.on("load", () => {
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

        map.addSource("nasaTrueColor", {
          type: "raster",
          tiles: [trueColorUrl],
          tileSize: 256,
          attribution: "NASA GIBS",
        });

        map.addLayer({
          id: "nasaTrueColor",
          type: "raster",
          source: "nasaTrueColor",
          layout: { visibility: "none" },
          paint: { "raster-opacity": 0.9, "raster-fade-duration": 100 },
        });

        map.addSource("nasaRain", {
          type: "raster",
          tiles: [rainUrl],
          tileSize: 256,
          attribution: "NASA GIBS and GPM IMERG",
        });

        map.addLayer({
          id: "nasaRain",
          type: "raster",
          source: "nasaRain",
          layout: { visibility: "visible" },
          paint: { "raster-opacity": 0.55, "raster-fade-duration": 100 },
        });

        setOverlayMessage("");
      } catch {
        setOverlayMessage("NASA map layers are temporarily unavailable. The field map still works.");
      }
    });

    map.on("error", () => {
      if (map.loaded()) {
        setOverlayMessage("Some map imagery could not load. You can still choose the field and load NASA data.");
      }
    });

    const resizeObserver = new ResizeObserver(() => map.resize());
    resizeObserver.observe(rootRef.current);

    mapRef.current = map;

    return () => {
      resizeObserver.disconnect();
      markerRef.current?.remove();
      markerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, [mapDate]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !point) return;

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
      zoom: Math.max(map.getZoom(), 9.4),
      pitch: reduceMotion ? 0 : 24,
      bearing: 0,
      duration: reduceMotion ? 0 : 900,
    });

    window.setTimeout(() => map.resize(), 120);
  }, [point]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const apply = () => {
      if (map.getLayer("nasaRain")) {
        map.setLayoutProperty("nasaRain", "visibility", rainVisible ? "visible" : "none");
      }
      if (map.getLayer("nasaTrueColor")) {
        map.setLayoutProperty("nasaTrueColor", "visibility", imageryVisible ? "visible" : "none");
      }
      if (map.getLayer("osm")) {
        map.setLayoutProperty("osm", "visibility", imageryVisible ? "none" : "visible");
      }
    };

    if (map.isStyleLoaded()) apply();
    else map.once("load", apply);
  }, [rainVisible, imageryVisible]);

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
        >
          <span className="chip-orb imagery" />
          NASA true color
        </button>

        <button
          type="button"
          className={rainVisible ? "map-chip active" : "map-chip"}
          onClick={() => setRainVisible((value) => !value)}
          aria-pressed={rainVisible}
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

      {overlayMessage && <div className="map-overlay-note">{overlayMessage}</div>}
    </div>
  );
}
