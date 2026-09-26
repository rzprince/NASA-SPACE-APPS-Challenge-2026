import { useEffect, useRef, useState } from "react";
import maplibregl, { type Map } from "maplibre-gl";
import type { Language } from "./api";

type Point = { latitude: number; longitude: number };

type Props = {
  point: Point | null;
  onPick: (point: Point) => void;
  language: Language;
  imergDate: string;
};

function copy(language: Language, en: string, bn: string) {
  return language === "bn" ? bn : en;
}

export default function LocationMap({ point, onPick, language, imergDate }: Props) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const onPickRef = useRef(onPick);
  const [rainVisible, setRainVisible] = useState(true);

  useEffect(() => {
    onPickRef.current = onPick;
  }, [onPick]);

  useEffect(() => {
    if (!rootRef.current || mapRef.current) return;

    const rainTiles =
      "https://gibs.earthdata.nasa.gov/wms/epsg3857/nrt/wms.cgi" +
      "?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0" +
      "&LAYERS=IMERG_Precipitation_Rate_v7_NRT" +
      "&STYLES=&FORMAT=image/png&TRANSPARENT=true" +
      "&HEIGHT=256&WIDTH=256&CRS=EPSG:3857" +
      `&TIME=${imergDate}&BBOX={bbox-epsg-3857}`;

    const map = new maplibregl.Map({
      container: rootRef.current,
      center: [90.35, 23.75],
      zoom: 5.55,
      minZoom: 4.8,
      maxZoom: 12,
      attributionControl: false,
      style: {
        version: 8,
        sources: {
          base: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
          imerg: {
            type: "raster",
            tiles: [rainTiles],
            tileSize: 256,
            attribution: "NASA GIBS · GPM IMERG",
          },
        },
        layers: [
          { id: "base", type: "raster", source: "base" },
          {
            id: "imerg",
            type: "raster",
            source: "imerg",
            paint: { "raster-opacity": 0.56, "raster-fade-duration": 120 },
          },
        ],
      },
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.addControl(
      new maplibregl.AttributionControl({ compact: true, customAttribution: "NASA GIBS" }),
      "bottom-right",
    );

    map.on("click", (event) => {
      onPickRef.current({
        latitude: Number(event.lngLat.lat.toFixed(5)),
        longitude: Number(event.lngLat.lng.toFixed(5)),
      });
    });

    mapRef.current = map;
    return () => {
      markerRef.current?.remove();
      markerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, [imergDate]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !point) return;
    if (!markerRef.current) {
      const element = document.createElement("div");
      element.className = "map-farm-marker";
      element.setAttribute("aria-hidden", "true");
      markerRef.current = new maplibregl.Marker({ element, anchor: "center" }).addTo(map);
    }
    markerRef.current.setLngLat([point.longitude, point.latitude]);
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    map.easeTo({
      center: [point.longitude, point.latitude],
      zoom: Math.max(map.getZoom(), 8),
      duration: reduceMotion ? 0 : 850,
    });
  }, [point]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = () => {
      if (map.getLayer("imerg")) {
        map.setLayoutProperty("imerg", "visibility", rainVisible ? "visible" : "none");
      }
    };
    if (map.isStyleLoaded()) apply();
    else map.once("load", apply);
  }, [rainVisible]);

  return (
    <div className="map-shell">
      <div ref={rootRef} className="location-map" aria-label={copy(language, "Interactive Bangladesh farm-location map", "বাংলাদেশের ইন্টার‌্যাক্টিভ জমির অবস্থান মানচিত্র")} />
      <div className="map-tools">
        <button
          type="button"
          className={rainVisible ? "layer-toggle active" : "layer-toggle"}
          onClick={() => setRainVisible((value) => !value)}
          aria-pressed={rainVisible}
        >
          <span className="layer-dot" />
          {copy(language, "Recent rainfall layer", "সাম্প্রতিক বৃষ্টির স্তর")}
        </button>
        <span className="layer-date">
          NASA IMERG · {imergDate}
        </span>
      </div>
      <div className="map-instruction">
        {copy(language, "Tap the map to choose your field area.", "আপনার জমির এলাকা বেছে নিতে মানচিত্রে ট্যাপ করুন।")}
      </div>
    </div>
  );
}
