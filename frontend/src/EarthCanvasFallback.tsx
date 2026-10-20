import { useEffect, useRef, useState } from "react";

type Point = { latitude: number; longitude: number };
type Props = {
  point: Point | null;
  onPick: (point: Point) => void;
};

// A real orthographic raster projection, not a flat image clipped to a circle.
// This stays selectable when a browser/device cannot create a WebGL2 context.
const BLUE_MARBLE = "https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57730/land_ocean_ice_2048.jpg";
const GIBS_BLUE_MARBLE =
  "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=BlueMarble_NextGeneration&STYLES=&FORMAT=image%2Fjpeg&TRANSPARENT=false&HEIGHT=512&WIDTH=1024&CRS=EPSG%3A4326&BBOX=-90%2C-180%2C90%2C180";
const DEG = Math.PI / 180;
const RAD = 180 / Math.PI;
const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
const wrapLongitude = (value: number) => ((((value + 180) % 360) + 360) % 360) - 180;

function inverseOrthographic(x: number, y: number, center: Point): Point | null {
  const rho = Math.hypot(x, y);
  if (rho > 1) return null;
  const lat0 = center.latitude * DEG;
  const c = Math.asin(clamp(rho, 0, 1));
  const sinC = Math.sin(c);
  const cosC = Math.cos(c);
  const latitude = Math.asin(clamp(cosC * Math.sin(lat0) + y * sinC * Math.cos(lat0) / (rho || 1), -1, 1)) * RAD;
  const longitude = center.longitude + Math.atan2(
    x * sinC,
    rho * Math.cos(lat0) * cosC - y * Math.sin(lat0) * sinC,
  ) * RAD;
  return { latitude, longitude: wrapLongitude(longitude) };
}

export default function EarthCanvasFallback({ point, onPick }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const centerRef = useRef<Point>({ latitude: 12, longitude: 20 });
  const zoomRef = useRef(1);
  const imageRef = useRef<ImageData | null>(null);
  const drawRef = useRef<() => void>(() => undefined);
  const onPickRef = useRef(onPick);
  const [imageStatus, setImageStatus] = useState("Loading NASA Blue Marble imagery…");

  useEffect(() => {
    onPickRef.current = onPick;
  }, [onPick]);

  useEffect(() => {
    if (point && Number.isFinite(point.latitude) && Number.isFinite(point.longitude)) {
      centerRef.current = { latitude: clamp(point.latitude, -90, 90), longitude: wrapLongitude(point.longitude) };
      drawRef.current();
    }
  }, [point]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const host = canvas?.parentElement;
    if (!canvas || !host) return;
    const context = canvas.getContext("2d", { alpha: false });
    if (!context) {
      setImageStatus("Canvas unavailable. Search or enter a place to choose a field.");
      return;
    }

    let stopped = false;
    let raf = 0;
    let currentImage: HTMLImageElement | null = null;
    let pointerStart: { id: number; x: number; y: number; moved: boolean } | null = null;
    const tile = document.createElement("canvas");
    const tileSize = 280;
    tile.width = tile.height = tileSize;
    const tileContext = tile.getContext("2d");
    const output = tileContext?.createImageData(tileSize, tileSize);

    const dimensions = () => {
      const width = canvas.clientWidth || host.clientWidth;
      const height = canvas.clientHeight || host.clientHeight;
      return { width, height, radius: Math.min(width * 0.42, height * 0.4, 335) * zoomRef.current };
    };

    function draw() {
      if (stopped || !context) return;
      const width = Math.max(1, Math.floor(canvas.clientWidth));
      const height = Math.max(1, Math.floor(canvas.clientHeight));
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }
      context.fillStyle = "#010705";
      context.fillRect(0, 0, width, height);

      // Stable stars; no animation loop and very low GPU/CPU requirements.
      context.fillStyle = "rgba(192,220,244,.64)";
      for (let i = 0; i < 145; i += 1) {
        const x = ((i * 1031.37) % 997) / 997 * width;
        const y = ((i * 719.53) % 991) / 991 * height;
        context.fillRect(x, y, i % 8 === 0 ? 1.5 : 1, i % 8 === 0 ? 1.5 : 1);
      }

      const { radius } = dimensions();
      const cx = width / 2;
      const cy = height / 2;
      const halo = context.createRadialGradient(cx, cy, radius * 0.8, cx, cy, radius * 1.21);
      halo.addColorStop(0, "rgba(32,121,172,.16)");
      halo.addColorStop(0.78, "rgba(17,128,193,.19)");
      halo.addColorStop(1, "rgba(10,93,159,0)");
      context.fillStyle = halo;
      context.beginPath();
      context.arc(cx, cy, radius * 1.21, 0, Math.PI * 2);
      context.fill();

      if (tileContext && output) {
        const pixels = output.data;
        const source = imageRef.current;
        const center = centerRef.current;
        for (let py = 0; py < tileSize; py += 1) {
          const y = 1 - (py + 0.5) * 2 / tileSize;
          for (let px = 0; px < tileSize; px += 1) {
            const x = (px + 0.5) * 2 / tileSize - 1;
            const dest = (py * tileSize + px) * 4;
            const p = inverseOrthographic(x, y, center);
            if (!p) {
              pixels[dest + 3] = 0;
              continue;
            }
            const z = Math.sqrt(Math.max(0, 1 - x * x - y * y));
            const light = clamp(0.30 + 0.84 * (0.23 * x + 0.2 * y + 0.8 * z), 0.17, 1);
            if (source) {
              const u = (p.longitude + 180) / 360;
              const v = (90 - p.latitude) / 180;
              const sx = clamp(Math.floor(u * source.width), 0, source.width - 1);
              const sy = clamp(Math.floor(v * source.height), 0, source.height - 1);
              const src = (sy * source.width + sx) * 4;
              pixels[dest] = source.data[src] * light;
              pixels[dest + 1] = source.data[src + 1] * light;
              pixels[dest + 2] = source.data[src + 2] * light;
            } else {
              // Explicit untextured ocean placeholder when remote imagery is offline.
              pixels[dest] = 10 * light;
              pixels[dest + 1] = 74 * light;
              pixels[dest + 2] = 124 * light;
            }
            pixels[dest + 3] = 255;
          }
        }
        tileContext.putImageData(output, 0, 0);
        context.drawImage(tile, cx - radius, cy - radius, radius * 2, radius * 2);
      }
      context.strokeStyle = "rgba(72,187,241,.48)";
      context.lineWidth = 1.2;
      context.beginPath();
      context.arc(cx, cy, radius, 0, Math.PI * 2);
      context.stroke();

      if (point) {
        context.strokeStyle = "rgba(184,255,87,.7)";
        context.fillStyle = "#b8ff57";
        context.lineWidth = 2;
        context.beginPath();
        context.arc(cx, cy, 14, 0, Math.PI * 2);
        context.stroke();
        context.beginPath();
        context.arc(cx, cy, 5, 0, Math.PI * 2);
        context.fill();
      }
    }

    const requestDraw = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(draw);
    };
    drawRef.current = requestDraw;

    function loadImage(urls: string[]) {
      if (stopped || !urls.length) {
        if (!stopped) setImageStatus("NASA imagery unavailable; coordinate globe remains selectable.");
        return;
      }
      const image = new Image();
      currentImage = image;
      image.crossOrigin = "anonymous";
      image.onload = () => {
        if (stopped) return;
        try {
          const buffer = document.createElement("canvas");
          buffer.width = image.naturalWidth;
          buffer.height = image.naturalHeight;
          const ctx = buffer.getContext("2d", { willReadFrequently: true });
          if (!ctx) throw new Error("No 2D texture context");
          ctx.drawImage(image, 0, 0);
          imageRef.current = ctx.getImageData(0, 0, buffer.width, buffer.height);
          setImageStatus("NASA Blue Marble · accessible 2D globe");
          requestDraw();
        } catch {
          loadImage(urls.slice(1));
        }
      };
      image.onerror = () => loadImage(urls.slice(1));
      image.src = urls[0];
    }

    const onDown = (event: PointerEvent) => {
      pointerStart = { id: event.pointerId, x: event.clientX, y: event.clientY, moved: false };
      canvas.setPointerCapture(event.pointerId);
    };
    const onMove = (event: PointerEvent) => {
      if (!pointerStart || pointerStart.id !== event.pointerId) return;
      const dx = event.clientX - pointerStart.x;
      const dy = event.clientY - pointerStart.y;
      if (Math.hypot(dx, dy) > 3) pointerStart.moved = true;
      const { radius } = dimensions();
      centerRef.current = {
        latitude: clamp(centerRef.current.latitude + dy / Math.max(radius, 1) * 85, -89.9, 89.9),
        longitude: wrapLongitude(centerRef.current.longitude - dx / Math.max(radius, 1) * 85),
      };
      pointerStart.x = event.clientX;
      pointerStart.y = event.clientY;
      requestDraw();
    };
    const onUp = (event: PointerEvent) => {
      if (!pointerStart || pointerStart.id !== event.pointerId) return;
      const moved = pointerStart.moved;
      pointerStart = null;
      if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
      if (!moved) {
        const rect = canvas.getBoundingClientRect();
        const { radius } = dimensions();
        const x = (event.clientX - rect.left - rect.width / 2) / radius;
        const y = (rect.height / 2 - (event.clientY - rect.top)) / radius;
        const picked = inverseOrthographic(x, y, centerRef.current);
        if (picked) onPickRef.current({
          latitude: Number(picked.latitude.toFixed(5)),
          longitude: Number(picked.longitude.toFixed(5)),
        });
      }
    };
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      zoomRef.current = clamp(zoomRef.current * (event.deltaY > 0 ? 0.92 : 1.08), 0.65, 1.25);
      requestDraw();
    };
    const resize = () => requestDraw();

    canvas.addEventListener("pointerdown", onDown);
    canvas.addEventListener("pointermove", onMove);
    canvas.addEventListener("pointerup", onUp);
    canvas.addEventListener("pointercancel", onUp);
    canvas.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("resize", resize);
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(resize);
    observer?.observe(host);
    loadImage([BLUE_MARBLE, GIBS_BLUE_MARBLE]);
    requestDraw();

    return () => {
      stopped = true;
      currentImage && (currentImage.onload = null);
      currentImage && (currentImage.onerror = null);
      cancelAnimationFrame(raf);
      observer?.disconnect();
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("pointerdown", onDown);
      canvas.removeEventListener("pointermove", onMove);
      canvas.removeEventListener("pointerup", onUp);
      canvas.removeEventListener("pointercancel", onUp);
      canvas.removeEventListener("wheel", onWheel);
      drawRef.current = () => undefined;
      imageRef.current = null;
    };
  }, []);

  return (
    <div className="earth-canvas-fallback">
      <canvas
        ref={canvasRef}
        tabIndex={0}
        role="button"
        aria-label="Accessible Earth globe. Drag to rotate, scroll to zoom, click to choose a coordinate, or press Enter to select the center."
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onPickRef.current(centerRef.current);
          }
        }}
      />
      <span className="earth-fallback-status">{imageStatus}</span>
    </div>
  );
}
