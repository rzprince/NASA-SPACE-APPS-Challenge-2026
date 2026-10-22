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
const NASA_BLUE_MARBLE =
  "https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57730/land_ocean_ice_2048.jpg";

function finitePoint(point: Point) {
  return Number.isFinite(point.latitude) && Number.isFinite(point.longitude);
}

function nasaGlobalWms(
  layer: string,
  date: string,
  format: "image/jpeg" | "image/png",
  transparent: boolean,
  width = 1024,
  height = 512,
) {
  const params = new URLSearchParams({
    SERVICE: "WMS",
    REQUEST: "GetMap",
    VERSION: "1.3.0",
    LAYERS: layer,
    STYLES: "",
    FORMAT: format,
    TRANSPARENT: transparent ? "true" : "false",
    HEIGHT: String(height),
    WIDTH: String(width),
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

function prepareTexture(texture: THREE.Texture, anisotropy = 4) {
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.ClampToEdgeWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  texture.anisotropy = anisotropy;
  texture.needsUpdate = true;
  return texture;
}

function makeOverlayMaterial() {
  return new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.FrontSide,
    uniforms: {
      uMap: { value: null as THREE.Texture | null },
      uOpacity: { value: 0.68 },
      uMaskDark: { value: 0 },
    },
    vertexShader: `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform sampler2D uMap;
      uniform float uOpacity;
      uniform float uMaskDark;
      varying vec2 vUv;

      void main() {
        vec4 color = texture2D(uMap, vUv);
        float luminance = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));
        float alpha = color.a * uOpacity;

        if (uMaskDark > 0.5) {
          alpha *= smoothstep(0.035, 0.13, luminance);
        }

        if (alpha < 0.025) discard;
        gl_FragColor = vec4(color.rgb, alpha);
      }
    `,
  });
}

export default function LocationMap({ point, onPick, mapDate, activeLayer, onLayerChange }: Props) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const sceneRef = useRef<{
    renderer: THREE.WebGLRenderer;
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    controls: OrbitControls;
    earth: THREE.Mesh<THREE.SphereGeometry, THREE.MeshStandardMaterial>;
    overlay: THREE.Mesh<THREE.SphereGeometry, THREE.ShaderMaterial>;
    labels: THREE.Mesh<THREE.SphereGeometry, THREE.MeshBasicMaterial>;
    marker: THREE.Group;
    raycaster: THREE.Raycaster;
    pointer: THREE.Vector2;
    desiredCamera: THREE.Vector3 | null;
    resumeTimer: number | null;
    cleanup: () => void;
  } | null>(null);

  const baseTextureRef = useRef<THREE.Texture | null>(null);
  const overlayTextureRef = useRef<THREE.Texture | null>(null);
  const labelTextureRef = useRef<THREE.Texture | null>(null);
  const onPickRef = useRef(onPick);
  const [ready, setReady] = useState(false);
  const [message, setMessage] = useState("");
  const [textureStatus, setTextureStatus] = useState("Loading NASA Blue Marble");

  const layerMeta = useMemo(
    () => ({
      trueColor: {
        label: "MODIS TRUE COLOR",
        detail: "dated Terra corrected reflectance laid over the complete Blue Marble base",
      },
      rain: {
        label: "GPM IMERG RAIN",
        detail: "dated precipitation visualization from NASA GIBS",
      },
      soil: {
        label: "SMAP SOIL MOISTURE",
        detail: "regional surface soil moisture visualization",
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
    let destroyed = false;

    try {
      THREE.Cache.enabled = true;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x010403);
      scene.fog = new THREE.FogExp2(0x010403, 0.028);

      const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 120);
      camera.position.set(0.35, 0.45, 6.75);

      const renderer = new THREE.WebGLRenderer({
        antialias: window.devicePixelRatio <= 1.35,
        alpha: false,
        powerPreference: "default",
      });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.3));
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.08;
      host.appendChild(renderer.domElement);

      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.052;
      controls.enablePan = false;
      controls.minDistance = 3.6;
      controls.maxDistance = 9.2;
      controls.rotateSpeed = 0.42;
      controls.zoomSpeed = 0.82;
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.22;

      const earthGeometry = new THREE.SphereGeometry(EARTH_RADIUS, 96, 64);
      const earthMaterial = new THREE.MeshStandardMaterial({
        color: 0x8aa095,
        roughness: 0.92,
        metalness: 0,
      });
      const earth = new THREE.Mesh(earthGeometry, earthMaterial);
      scene.add(earth);

      const overlayMaterial = makeOverlayMaterial();
      const overlay = new THREE.Mesh(
        new THREE.SphereGeometry(EARTH_RADIUS + 0.014, 96, 64),
        overlayMaterial,
      );
      overlay.visible = false;
      scene.add(overlay);

      const labelsMaterial = new THREE.MeshBasicMaterial({
        transparent: true,
        opacity: 0,
        depthWrite: false,
        alphaTest: 0.03,
      });
      const labels = new THREE.Mesh(
        new THREE.SphereGeometry(EARTH_RADIUS + 0.025, 96, 64),
        labelsMaterial,
      );
      labels.visible = false;
      scene.add(labels);

      const atmosphere = new THREE.Mesh(
        new THREE.SphereGeometry(EARTH_RADIUS + 0.085, 72, 48),
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
              float intensity = pow(0.73 - dot(vNormal, vPositionNormal), 2.35);
              vec3 glow = vec3(0.18, 0.72, 0.95) * intensity;
              gl_FragColor = vec4(glow, intensity * 0.52);
            }
          `,
        }),
      );
      scene.add(atmosphere);

      scene.add(new THREE.HemisphereLight(0xdce9ff, 0x07110d, 1.38));
      const sun = new THREE.DirectionalLight(0xffffff, 2.28);
      sun.position.set(6.5, 3.1, 7.8);
      scene.add(sun);
      const rim = new THREE.DirectionalLight(0x4bdcff, 0.72);
      rim.position.set(-7, 0.4, -5);
      scene.add(rim);

      const starGeometry = new THREE.BufferGeometry();
      const starCount = 760;
      const starPositions = new Float32Array(starCount * 3);
      for (let index = 0; index < starCount; index += 1) {
        const radius = 22 + Math.random() * 52;
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
          color: 0xc7dcff,
          size: 0.026,
          transparent: true,
          opacity: 0.67,
          depthWrite: false,
        }),
      );
      scene.add(stars);

      const orbitMaterial = new THREE.LineBasicMaterial({
        color: 0x5eb39e,
        transparent: true,
        opacity: 0.18,
      });
      [3.06, 3.34].forEach((radius, index) => {
        const points: THREE.Vector3[] = [];
        for (let step = 0; step <= 120; step += 1) {
          const angle = (step / 120) * Math.PI * 2;
          points.push(
            new THREE.Vector3(
              Math.cos(angle) * radius,
              Math.sin(angle) * radius * 0.25,
              Math.sin(angle) * radius * 0.64,
            ),
          );
        }
        const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), orbitMaterial.clone());
        line.rotation.x = 0.38 + index * 0.26;
        line.rotation.z = 0.16 + index * 0.34;
        scene.add(line);
      });

      const marker = new THREE.Group();
      const markerCore = new THREE.Mesh(
        new THREE.SphereGeometry(0.052, 20, 14),
        new THREE.MeshBasicMaterial({ color: 0xb8ff57 }),
      );
      const markerHalo = new THREE.Mesh(
        new THREE.RingGeometry(0.095, 0.128, 44),
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
        new THREE.CylinderGeometry(0.006, 0.024, 0.38, 10),
        new THREE.MeshBasicMaterial({
          color: 0x64e6ff,
          transparent: true,
          opacity: 0.68,
        }),
      );
      markerBeam.position.y = 0.18;
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

      const resumeRotationLater = () => {
        const state = sceneRef.current;
        if (!state) return;
        if (state.resumeTimer) window.clearTimeout(state.resumeTimer);
        state.resumeTimer = window.setTimeout(() => {
          const current = sceneRef.current;
          if (current && !current.desiredCamera) current.controls.autoRotate = true;
        }, 5000);
      };

      const handlePointerDown = (event: PointerEvent) => {
        pointerDown = { x: event.clientX, y: event.clientY };
        controls.autoRotate = false;
      };

      const handlePointerUp = (event: PointerEvent) => {
        const moved = Math.hypot(event.clientX - pointerDown.x, event.clientY - pointerDown.y);
        if (moved <= 5) {
          const rect = renderer.domElement.getBoundingClientRect();
          pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
          pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
          raycaster.setFromCamera(pointer, camera);
          const hit = raycaster.intersectObject(earth, false)[0];
          if (hit) {
            const nextPoint = vectorToLatLon(hit.point);
            if (finitePoint(nextPoint)) onPickRef.current(nextPoint);
          }
        }
        resumeRotationLater();
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
        labels,
        marker,
        raycaster,
        pointer,
        desiredCamera: null,
        resumeTimer: null,
        cleanup: () => {
          observer.disconnect();
          renderer.domElement.removeEventListener("pointerdown", handlePointerDown);
          renderer.domElement.removeEventListener("pointerup", handlePointerUp);
          controls.dispose();
          earth.geometry.dispose();
          earth.material.dispose();
          overlay.geometry.dispose();
          overlay.material.dispose();
          labels.geometry.dispose();
          labels.material.dispose();
          starGeometry.dispose();
          (stars.material as THREE.Material).dispose();
          renderer.dispose();
          if (renderer.domElement.parentNode === host) host.removeChild(renderer.domElement);
        },
      };

      const loader = new THREE.TextureLoader();
      loader.setCrossOrigin("anonymous");

      const applyBaseTexture = (texture: THREE.Texture, label: string) => {
        if (destroyed || !sceneRef.current) {
          texture.dispose();
          return;
        }
        baseTextureRef.current?.dispose();
        baseTextureRef.current = prepareTexture(texture, renderer.capabilities.getMaxAnisotropy());
        sceneRef.current.earth.material.map = baseTextureRef.current;
        sceneRef.current.earth.material.color.set(0xffffff);
        sceneRef.current.earth.material.needsUpdate = true;
        setTextureStatus(label);
      };

      const fallbackBlueMarble = nasaGlobalWms(
        "BlueMarble_NextGeneration",
        "",
        "image/jpeg",
        false,
        1024,
        512,
      );

      loader.load(
        NASA_BLUE_MARBLE,
        (texture) => applyBaseTexture(texture, "NASA Blue Marble ready"),
        undefined,
        () => {
          loader.load(
            fallbackBlueMarble,
            (texture) => applyBaseTexture(texture, "NASA Blue Marble ready"),
            undefined,
            () => {
              setTextureStatus("NASA Blue Marble unavailable");
              setMessage("The NASA Earth texture could not load. Field search and coordinates still work.");
            },
          );
        },
      );

      const labelsUrl = nasaGlobalWms("Reference_Labels", "", "image/png", true, 2048, 1024);
      loader.load(
        labelsUrl,
        (texture) => {
          if (destroyed || !sceneRef.current) {
            texture.dispose();
            return;
          }
          labelTextureRef.current?.dispose();
          labelTextureRef.current = prepareTexture(texture);
          sceneRef.current.labels.material.map = labelTextureRef.current;
          sceneRef.current.labels.material.needsUpdate = true;
          sceneRef.current.labels.visible = true;
        },
        undefined,
        () => undefined,
      );

      const clock = new THREE.Clock();
      const animate = () => {
        const state = sceneRef.current;
        if (!state) return;

        const elapsed = clock.getElapsedTime();
        state.controls.update();

        if (state.desiredCamera) {
          camera.position.lerp(state.desiredCamera, 0.075);
          if (camera.position.distanceTo(state.desiredCamera) < 0.035) {
            state.desiredCamera = null;
            resumeRotationLater();
          }
        }

        const distance = camera.position.length();
        state.labels.material.opacity = THREE.MathUtils.clamp((6.5 - distance) / 1.7, 0.12, 0.92);
        markerHalo.scale.setScalar(1 + Math.sin(elapsed * 2.3) * 0.1);
        (markerHalo.material as THREE.MeshBasicMaterial).opacity = 0.58 + (Math.sin(elapsed * 2.3) + 1) * 0.11;
        stars.rotation.y = elapsed * 0.0016;
        renderer.render(scene, camera);
        raf = requestAnimationFrame(animate);
      };
      animate();
      setReady(true);
    } catch {
      setMessage("The 3D Earth view could not start. Place search and current location are still available.");
      setReady(false);
    }

    return () => {
      destroyed = true;
      cancelAnimationFrame(raf);
      if (sceneRef.current?.resumeTimer) window.clearTimeout(sceneRef.current.resumeTimer);
      baseTextureRef.current?.dispose();
      overlayTextureRef.current?.dispose();
      labelTextureRef.current?.dispose();
      baseTextureRef.current = null;
      overlayTextureRef.current = null;
      labelTextureRef.current = null;
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

    if (!activeLayer) {
      state.overlay.visible = false;
      overlayTextureRef.current?.dispose();
      overlayTextureRef.current = null;
      state.overlay.material.uniforms.uMap.value = null;
      setTextureStatus("NASA Blue Marble ready");
      setMessage("");
      return;
    }

    const urls: Record<LayerKey, { url: string; maskDark: boolean; opacity: number }> = {
      trueColor: {
        url: nasaGlobalWms("MODIS_Terra_CorrectedReflectance_TrueColor", mapDate, "image/jpeg", false),
        maskDark: true,
        opacity: 0.74,
      },
      rain: {
        url: nasaGlobalWms("IMERG_Precipitation_Rate", mapDate, "image/png", true),
        maskDark: false,
        opacity: 0.72,
      },
      soil: {
        url: nasaGlobalWms("SMAP_L2_Passive_Day_Soil_Moisture_Option2", mapDate, "image/png", true),
        maskDark: false,
        opacity: 0.72,
      },
    };

    const config = urls[activeLayer];
    setTextureStatus(`Loading ${layerMeta[activeLayer].label}`);
    setMessage("");

    loader.load(
      config.url,
      (texture) => {
        if (cancelled || !sceneRef.current) {
          texture.dispose();
          return;
        }
        overlayTextureRef.current?.dispose();
        overlayTextureRef.current = prepareTexture(texture);
        const material = sceneRef.current.overlay.material;
        material.uniforms.uMap.value = overlayTextureRef.current;
        material.uniforms.uOpacity.value = config.opacity;
        material.uniforms.uMaskDark.value = config.maskDark ? 1 : 0;
        material.needsUpdate = true;
        sceneRef.current.overlay.visible = true;
        setTextureStatus(`${layerMeta[activeLayer].label} ready`);
      },
      undefined,
      () => {
        if (!cancelled && sceneRef.current) {
          sceneRef.current.overlay.visible = false;
          setTextureStatus(`${layerMeta[activeLayer].label} unavailable`);
          setMessage("This optional NASA overlay is unavailable for the selected date. The complete NASA Blue Marble Earth and field analysis remain active.");
        }
      },
    );

    return () => {
      cancelled = true;
    };
  }, [activeLayer, layerMeta, mapDate, ready]);

  useEffect(() => {
    const state = sceneRef.current;
    if (!state || !point || !finitePoint(point)) return;

    const surface = latLonToVector(point.latitude, point.longitude, EARTH_RADIUS + 0.075);
    const normal = surface.clone().normalize();
    state.marker.visible = true;
    state.marker.position.copy(surface);
    state.marker.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal);

    state.controls.autoRotate = false;
    state.desiredCamera = normal.clone().multiplyScalar(4.95);
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
        <small>{activeLayer ? layerMeta[activeLayer].detail : "complete global NASA reference imagery"}</small>
      </div>

      <div className="globe-date">
        {activeLayer ? "NASA layer date" : "Earth reference"}
        <strong>{activeLayer ? mapDate : "Blue Marble"}</strong>
      </div>

      <div className="globe-interaction-tip">DRAG TO ROTATE · SCROLL TO ZOOM · TAP TO SELECT · LABELS APPEAR CLOSER</div>
      {message && <div className="globe-message compact">{message}</div>}
    </div>
  );
}
