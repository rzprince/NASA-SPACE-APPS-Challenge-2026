import { useEffect, useMemo, useRef, useState } from "react";
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
  const [imageryVisible, setImageryVisible] = useState(false);

  const urls = useMemo(() => {
    const bbox = "{bbox-epsg-3857}";
    const imerg =
      "https://gibs.earthdata.nasa.gov/wms/epsg3857/nrt/wms.cgi" +
      "?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0" +
      "&LAYERS=IMERG_Precipitation_Rate_v7_NRT" +
      "&STYLES=&FORMAT=image/png&TRANSPARENT=true" +
      "&HEIGHT=256&WIDTH=256&CRS=EPSG:3857" +
      `&TIME=${imergDate}&BBOX=${bbox}`;

    const trueColor =
      "https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi" +
      "?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0" +
      "&LAYERS=MODIS_Terra_CorrectedReflectance_TrueColor" +
      "&STYLES=&FORMAT=image/jpeg&TRANSPARENT=false" +
      "&HEIGHT=256&WIDTH=256&CRS=EPSG:3857" +
      `&TIME=${imergDate}&BBOX=${bbox}`;

    return { imerg, trueColor };
  }, [imergDate]);

  useEffect(() => {
    onPickRef.current = onPick;
  }, [onPick]);

  useEffect(() => {
    if (!rootRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: rootRef.current,
      center: [90.32, 23.76],
      zoom: 5.5,
      minZoom: 4.6,
      maxZoom: 13,
      attributionControl: false,
      style: {
        version: 8,
        sources: {
          street: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
          nasaTrueColor: {
            type: "raster",
            tiles: [urls.trueColor],
            tileSize: 256,
            attribution: "NASA GIBS",
          },
          nasaRain: {
            type: "raster",
            tiles: [urls.imerg],
            tileSize: 256,
            attribution: "NASA GIBS · GPM IMERG",
          },
        },
        layers: [
          { id: "street", type: "raster", source: "street" },
          {
            id: "nasaTrueColor",
            type: "raster",
            source: "nasaTrueColor",
            layout: { visibility: "none" },
            paint: { "raster-opacity": 0.88, "raster-fade-duration": 150 },
          },
          {
            id: "nasaRain",
            type: "raster",
            source: "nasaRain",
            paint: { "raster-opacity": 0.58, "raster-fade-duration": 120 },
          },
        ],
      },
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), "top-right");
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
  }, [urls.imerg, urls.trueColor]);

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
      zoom: Math.max(map.getZoom(), 9),
      pitch: reduceMotion ? 0 : 28,
      bearing: reduceMotion ? 0 : -8,
      duration: reduceMotion ? 0 : 1100,
    });
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
      if (map.getLayer("street")) {
        map.setLayoutProperty("street", "visibility", imageryVisible ? "none" : "visible");
      }
    };
    if (map.isStyleLoaded()) apply();
    else map.once("load", apply);
  }, [rainVisible, imageryVisible]);

  return (
    <div className="map-stage">
      <div ref={rootRef} className="field-map" aria-label={copy(language, "Interactive Bangladesh farm map", "বাংলাদেশের ইন্টার‌্যাক্টিভ কৃষিজমির মানচিত্র")} />
      <div className="map-vignette" aria-hidden="true" />
      <div className="map-toolbar">
        <button
          type="button"
          className={imageryVisible ? "map-chip active" : "map-chip"}
          onClick={() => setImageryVisible((value) => !value)}
          aria-pressed={imageryVisible}
        >
          <span className="chip-orb imagery" />
          {copy(language, "NASA true color", "NASA ট্রু-কালার")}
        </button>
        <button
          type="button"
          className={rainVisible ? "map-chip active" : "map-chip"}
          onClick={() => setRainVisible((value) => !value)}
          aria-pressed={rainVisible}
        >
          <span className="chip-orb rain" />
          {copy(language, "IMERG rain", "IMERG বৃষ্টি")}
        </button>
      </div>
      <div className="map-date">
        <span>{copy(language, "NASA layer date", "NASA স্তরের তারিখ")}</span>
        <strong>{imergDate}</strong>
      </div>
      <div className="map-help">
        <span className="map-help-dot" />
        {copy(language, "Tap anywhere in Bangladesh to set the field point", "বাংলাদেশের যেকোনো স্থানে ট্যাপ করে জমির পয়েন্ট নির্ধারণ করুন")}
      </div>
    </div>
  );
}
