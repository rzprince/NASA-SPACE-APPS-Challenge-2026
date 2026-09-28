import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

type Point = { latitude: number; longitude: number };
type LayerKey = "trueColor" | "rain" | "soil";

type Props = {
  point: Point | null;
  onPick: (point: Point) => void;
  mapDate: string;
  activeLayer: LayerKey | null;
  onLayerChange: (layer: LayerKey | null) => void;
};

const EARTH_RADIUS = 2.5;

function finitePoint(point: Point) {
  return Number.isFinite(point.latitude) && Number.isFinite(point.longitude);
}

function nasaGlobalWms(layer: string, date: string, format: "image/jpeg" | "image/png", transparent: boolean) {
  const params = new URLSearchParams({
    SERVICE: "WMS",
    REQUEST: "GetMap",
    VERSION: "1.3.0",
    LAYERS: layer,
    STYLES: "",
    FORMAT: format,
    TRANSPARENT: transparent ? "true" : "false",
    HEIGHT: "1024",
    WIDTH: "2048",
    CRS: "EPSG:4326",
    BBOX: "-90,-180,90,180",
  });
  if (date) params.set("TIME", date);
  return `https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?${params.toString()}`;
}

function latLonToVector(latitude: number, longitude: number, radius = EARTH_RADIUS) {
  const lat = THREE.MathUtils.degToRad(latitude);
  const lon = THREE.MathUtils.degToRad(longitude);
  return new THREE.Vector3(
    -radius * Math.cos(lat) * Math.cos(lon),
    radius * Math.sin(lat),
    radius * Math.cos(lat) * Math.sin(lon),
  );
}

function vectorToLatLon(vector: THREE.Vector3): Point {
  const normal = vector.clone().normalize();
  const latitude = THREE.MathUtils.radToDeg(Math.asin(THREE.MathUtils.clamp(normal.y, -1, 1)));
  const longitude = THREE.MathUtils.radToDeg(Math.atan2(normal.z, -normal.x));
  return {
    latitude: Number(latitude.toFixed(5)),
    longitude: Number(longitude.toFixed(5)),
  };
}

function prepareTexture(texture: THREE.Texture) {
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.offset.x = 0.5;
  texture.anisotropy = 4;
  texture.needsUpdate = true;
  return texture;
}

export default function LocationMap({ point, onPick, mapDate, activeLayer, onLayerChange }: Props) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const sceneRef = useRef<{
    renderer: THREE.WebGLRenderer;
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    controls: OrbitControls;
    earth: THREE.Mesh<THREE.SphereGeometry, THREE.MeshStandardMaterial>;
    overlay: THREE.Mesh<THREE.SphereGeometry, THREE.MeshBasicMaterial>;
    marker: THREE.Group;
    raycaster: THREE.Raycaster;
    pointer: THREE.Vector2;
    desiredCamera: THREE.Vector3 | null;
    cleanup: () => void;
  } | null>(null);
  const baseTextureRef = useRef<THREE.Texture | null>(null);
  const overlayTextureRef = useRef<THREE.Texture | null>(null);
  const onPickRef = useRef(onPick);
  const [ready, setReady] = useState(false);
  const [message, setMessage] = useState("");
  const [textureStatus, setTextureStatus] = useState("Loading NASA Earth imagery");

  const layerMeta = useMemo(
    () => ({
      trueColor: {
        label: "NASA TRUE COLOR",
        detail: "MODIS Terra corrected reflectance",
      },
      rain: {
        label: "IMERG RAIN",
        detail: "GPM IMERG V07 precipitation layer",
      },
      soil: {
        label: "SMAP SOIL",
        detail: "SMAP surface soil moisture layer",
      },
    }),
    [],
  );

  useEffect(() => {
    onPickRef.current = onPick;
  }, [onPick]);

  useEffect(() => {
    const host = rootRef.current;
    if (!host || sceneRef.current) return;

    let raf = 0;
    let pointerDown = { x: 0, y: 0 };

    try {
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x010403);
      scene.fog = new THREE.FogExp2(0x010403, 0.035);

      const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 120);
      camera.position.set(0.2, 0.55, 6.8);

      const renderer = new THREE.WebGLRenderer({
        antialias: window.devicePixelRatio <= 1.5,
        alpha: false,
        powerPreference: "high-performance",
      });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.05;
      host.appendChild(renderer.domElement);

      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.055;
      controls.enablePan = false;
      controls.minDistance = 3.75;
      controls.maxDistance = 9.5;
      controls.rotateSpeed = 0.45;
      controls.zoomSpeed = 0.8;
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.18;

      const earthGeometry = new THREE.SphereGeometry(EARTH_RADIUS, 128, 96);
      const earthMaterial = new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.9,
        metalness: 0,
      });
      const earth = new THREE.Mesh(earthGeometry, earthMaterial);
      scene.add(earth);

      const overlayMaterial = new THREE.MeshBasicMaterial({
        transparent: true,
        opacity: 0.74,
        depthWrite: false,
        blending: THREE.NormalBlending,
      });
      const overlay = new THREE.Mesh(
        new THREE.SphereGeometry(EARTH_RADIUS + 0.012, 128, 96),
        overlayMaterial,
      );
      overlay.visible = false;
      scene.add(overlay);

      const atmosphere = new THREE.Mesh(
        new THREE.SphereGeometry(EARTH_RADIUS + 0.08, 96, 64),
        new THREE.ShaderMaterial({
          transparent: true,
          side: THREE.BackSide,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
          vertexShader: `
            varying vec3 vNormal;
            varying vec3 vPositionNormal;
            void main() {
              vNormal = normalize(normalMatrix * normal);
              vPositionNormal = normalize((modelViewMatrix * vec4(position, 1.0)).xyz);
              gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
          `,
          fragmentShader: `
            varying vec3 vNormal;
            varying vec3 vPositionNormal;
            void main() {
              float intensity = pow(0.72 - dot(vNormal, vPositionNormal), 2.4);
              vec3 glow = vec3(0.18, 0.72, 0.95) * intensity;
              gl_FragColor = vec4(glow, intensity * 0.56);
            }
          `,
        }),
      );
      scene.add(atmosphere);

      const ambient = new THREE.AmbientLight(0xa8c2b4, 1.5);
      scene.add(ambient);
      const sun = new THREE.DirectionalLight(0xffffff, 2.65);
      sun.position.set(7, 3.5, 8);
      scene.add(sun);
      const rim = new THREE.DirectionalLight(0x4bdcff, 0.9);
      rim.position.set(-7, 0, -5);
      scene.add(rim);

      const starGeometry = new THREE.BufferGeometry();
      const starCount = 1200;
      const starPositions = new Float32Array(starCount * 3);
      for (let index = 0; index < starCount; index += 1) {
        const radius = 22 + Math.random() * 55;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        starPositions[index * 3] = radius * Math.sin(phi) * Math.cos(theta);
        starPositions[index * 3 + 1] = radius * Math.cos(phi);
        starPositions[index * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
      }
      starGeometry.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
      const stars = new THREE.Points(
        starGeometry,
        new THREE.PointsMaterial({
          color: 0xb8d8ff,
          size: 0.027,
          transparent: true,
          opacity: 0.72,
          depthWrite: false,
        }),
      );
      scene.add(stars);

      const orbitMaterial = new THREE.LineBasicMaterial({
        color: 0x5eb39e,
        transparent: true,
        opacity: 0.22,
      });
      [3.05, 3.32, 3.63].forEach((radius, index) => {
        const points: THREE.Vector3[] = [];
        for (let step = 0; step <= 160; step += 1) {
          const angle = (step / 160) * Math.PI * 2;
          points.push(new THREE.Vector3(Math.cos(angle) * radius, Math.sin(angle) * radius * 0.26, Math.sin(angle) * radius * 0.64));
        }
        const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), orbitMaterial.clone());
        line.rotation.x = 0.35 + index * 0.24;
        line.rotation.z = 0.18 + index * 0.31;
        scene.add(line);
      });

      const marker = new THREE.Group();
      const markerCore = new THREE.Mesh(
        new THREE.SphereGeometry(0.055, 24, 18),
        new THREE.MeshBasicMaterial({ color: 0xb8ff57 }),
      );
      const markerHalo = new THREE.Mesh(
        new THREE.RingGeometry(0.095, 0.125, 48),
        new THREE.MeshBasicMaterial({
          color: 0xb8ff57,
          transparent: true,
          opacity: 0.82,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      );
      markerHalo.rotation.x = Math.PI / 2;
      const markerBeam = new THREE.Mesh(
        new THREE.CylinderGeometry(0.006, 0.026, 0.42, 12),
        new THREE.MeshBasicMaterial({
          color: 0x64e6ff,
          transparent: true,
          opacity: 0.72,
        }),
      );
      markerBeam.position.y = 0.19;
      marker.add(markerCore, markerHalo, markerBeam);
      marker.visible = false;
      scene.add(marker);

      const raycaster = new THREE.Raycaster();
      const pointer = new THREE.Vector2();

      const resize = () => {
        const rect = host.getBoundingClientRect();
        const width = Math.max(rect.width, 1);
        const height = Math.max(rect.height, 1);
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
      };

      const handlePointerDown = (event: PointerEvent) => {
        pointerDown = { x: event.clientX, y: event.clientY };
        controls.autoRotate = false;
      };

      const handlePointerUp = (event: PointerEvent) => {
        const moved = Math.hypot(event.clientX - pointerDown.x, event.clientY - pointerDown.y);
        if (moved > 5) return;

        const rect = renderer.domElement.getBoundingClientRect();
        pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(pointer, camera);
        const hit = raycaster.intersectObject(earth, false)[0];
        if (!hit) return;
        const nextPoint = vectorToLatLon(hit.point);
        if (finitePoint(nextPoint)) onPickRef.current(nextPoint);
      };

      renderer.domElement.addEventListener("pointerdown", handlePointerDown);
      renderer.domElement.addEventListener("pointerup", handlePointerUp);

      const observer = new ResizeObserver(() => requestAnimationFrame(resize));
      observer.observe(host);
      resize();

      sceneRef.current = {
        renderer,
        scene,
        camera,
        controls,
        earth,
        overlay,
        marker,
        raycaster,
        pointer,
        desiredCamera: null,
        cleanup: () => {
          observer.disconnect();
          renderer.domElement.removeEventListener("pointerdown", handlePointerDown);
          renderer.domElement.removeEventListener("pointerup", handlePointerUp);
          controls.dispose();
          earth.geometry.dispose();
          earth.material.dispose();
          overlay.geometry.dispose();
          overlay.material.dispose();
          starGeometry.dispose();
          (stars.material as THREE.Material).dispose();
          renderer.dispose();
          renderer.domElement.remove();
        },
      };

      const clock = new THREE.Clock();
      const animate = () => {
        const state = sceneRef.current;
        if (!state) return;
        const elapsed = clock.getElapsedTime();
        controls.update();

        if (state.desiredCamera) {
          camera.position.lerp(state.desiredCamera, 0.07);
          if (camera.position.distanceTo(state.desiredCamera) < 0.03) {
            state.desiredCamera = null;
          }
        }

        markerHalo.scale.setScalar(1 + Math.sin(elapsed * 2.4) * 0.12);
        markerHalo.material.opacity = 0.58 + (Math.sin(elapsed * 2.4) + 1) * 0.12;
        stars.rotation.y = elapsed * 0.0022;
        renderer.render(scene, camera);
        raf = requestAnimationFrame(animate);
      };
      animate();
      setReady(true);
    } catch {
      setMessage("The realistic 3D Earth view could not start. Use place search or current location to continue.");
      setReady(false);
    }

    return () => {
      cancelAnimationFrame(raf);
      baseTextureRef.current?.dispose();
      overlayTextureRef.current?.dispose();
      baseTextureRef.current = null;
      overlayTextureRef.current = null;
      sceneRef.current?.cleanup();
      sceneRef.current = null;
    };
  }, []);

  useEffect(() => {
    const state = sceneRef.current;
    if (!state || !ready) return;

    let cancelled = false;
    const loader = new THREE.TextureLoader();
    loader.setCrossOrigin("anonymous");

    const blueMarble = nasaGlobalWms("BlueMarble_NextGeneration", "", "image/jpeg", false);
    const trueColor = nasaGlobalWms("MODIS_Terra_CorrectedReflectance_TrueColor", mapDate, "image/jpeg", false);
    const rain = nasaGlobalWms("IMERG_Precipitation_Rate_v7_STD", mapDate, "image/png", true);
    const soil = nasaGlobalWms("SMAP_L2_Passive_Day_Soil_Moisture_Option2", mapDate, "image/png", true);

    const baseUrl = activeLayer === "trueColor" ? trueColor : blueMarble;
    const overlayUrl = activeLayer === "rain" ? rain : activeLayer === "soil" ? soil : null;

    setTextureStatus(activeLayer ? `Loading ${layerMeta[activeLayer].label}` : "Loading NASA Blue Marble");
    setMessage("");

    loader.load(
      baseUrl,
      (texture) => {
        if (cancelled || !sceneRef.current) {
          texture.dispose();
          return;
        }
        baseTextureRef.current?.dispose();
        baseTextureRef.current = prepareTexture(texture);
        sceneRef.current.earth.material.map = baseTextureRef.current;
        sceneRef.current.earth.material.color.set(0xffffff);
        sceneRef.current.earth.material.needsUpdate = true;
        setTextureStatus(activeLayer === "trueColor" ? "NASA true color loaded" : "NASA Blue Marble loaded");
      },
      undefined,
      () => {
        if (!cancelled) {
          setTextureStatus("NASA imagery fallback");
          setMessage("NASA Earth texture is temporarily unavailable. The globe remains selectable and field analysis still works.");
        }
      },
    );

    if (overlayUrl) {
      loader.load(
        overlayUrl,
        (texture) => {
          if (cancelled || !sceneRef.current) {
            texture.dispose();
            return;
          }
          overlayTextureRef.current?.dispose();
          overlayTextureRef.current = prepareTexture(texture);
          sceneRef.current.overlay.material.map = overlayTextureRef.current;
          sceneRef.current.overlay.material.needsUpdate = true;
          sceneRef.current.overlay.visible = true;
          setTextureStatus(`${layerMeta[activeLayer!].label} loaded`);
        },
        undefined,
        () => {
          if (!cancelled && sceneRef.current) {
            sceneRef.current.overlay.visible = false;
            setMessage("The selected NASA overlay could not load. NASA Blue Marble and field selection remain available.");
          }
        },
      );
    } else {
      state.overlay.visible = false;
      overlayTextureRef.current?.dispose();
      overlayTextureRef.current = null;
      state.overlay.material.map = null;
      state.overlay.material.needsUpdate = true;
    }

    return () => {
      cancelled = true;
    };
  }, [activeLayer, layerMeta, mapDate, ready]);

  useEffect(() => {
    const state = sceneRef.current;
    if (!state || !point || !finitePoint(point)) return;

    const surface = latLonToVector(point.latitude, point.longitude, EARTH_RADIUS + 0.08);
    const normal = surface.clone().normalize();
    state.marker.visible = true;
    state.marker.position.copy(surface);
    state.marker.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal);

    const targetDistance = 5.25;
    state.desiredCamera = normal.multiplyScalar(targetDistance);
    state.controls.autoRotate = false;
  }, [point]);

  return (
    <div className="earth-globe-stage realistic-earth">
      <div ref={rootRef} className="earth-globe-map" aria-label="Interactive realistic 3D NASA Earth field selector" />

      <div className="globe-hud">
        <span className="hud-label">EARTH TWIN</span>
        <span>{point ? `${point.latitude.toFixed(4)}°, ${point.longitude.toFixed(4)}°` : "Rotate Earth. Tap any land area."}</span>
      </div>

      <div className="space-view-label">
        <span className="space-view-kicker">NASA EARTH VIEW</span>
        <strong>{point ? "Field locked" : "Select a field anywhere on Earth"}</strong>
        <small>{textureStatus}</small>
      </div>

      <div className="layer-switcher" aria-label="NASA spatial layers">
        {([
          ["trueColor", "TRUE COLOR"],
          ["rain", "IMERG RAIN"],
          ["soil", "SMAP SOIL"],
        ] as const).map(([key, label]) => (
          <button
            type="button"
            key={key}
            className={activeLayer === key ? "active" : ""}
            onClick={() => onLayerChange(activeLayer === key ? null : key)}
            disabled={!ready}
          >
            <i />
            {label}
          </button>
        ))}
      </div>

      <div className="globe-layer-detail">
        <span>{activeLayer ? layerMeta[activeLayer].label : "NASA BLUE MARBLE"}</span>
        <small>{activeLayer ? layerMeta[activeLayer].detail : "global Earth reference imagery"}</small>
      </div>

      <div className="globe-date">NASA layer date <strong>{mapDate}</strong></div>
      <div className="globe-interaction-tip">DRAG TO ROTATE · SCROLL TO ZOOM · TAP TO SELECT</div>
      {message && <div className="globe-message">{message}</div>}
    </div>
  );
}
