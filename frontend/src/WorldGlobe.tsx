import { useEffect, useRef } from "react";
import * as THREE from "three";

type Point = { latitude: number; longitude: number };

type Props = {
  point: Point | null;
  onPick: (point: Point) => void;
  className?: string;
};

function sphericalPoint(latitude: number, longitude: number, radius: number) {
  const phi = THREE.MathUtils.degToRad(90 - latitude);
  const theta = THREE.MathUtils.degToRad(longitude);
  return new THREE.Vector3(
    radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  );
}

export default function WorldGlobe({ point, onPick, className = "" }: Props) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const onPickRef = useRef(onPick);
  const pointRef = useRef(point);

  useEffect(() => {
    onPickRef.current = onPick;
  }, [onPick]);

  useEffect(() => {
    pointRef.current = point;
  }, [point]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
    camera.position.set(0, 0.25, 7.7);

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: window.devicePixelRatio <= 1.5,
      powerPreference: "default",
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.35));
    renderer.setClearColor(0x000000, 0);
    host.appendChild(renderer.domElement);

    const earth = new THREE.Group();
    earth.rotation.x = -0.14;
    earth.rotation.y = -1.45;
    scene.add(earth);

    const radius = 2.25;
    const globe = new THREE.Mesh(
      new THREE.SphereGeometry(radius, 72, 48),
      new THREE.MeshPhongMaterial({
        color: 0x0a2130,
        emissive: 0x031017,
        shininess: 24,
        transparent: true,
        opacity: 0.98,
      }),
    );
    earth.add(globe);

    const wire = new THREE.Mesh(
      new THREE.SphereGeometry(radius * 1.006, 36, 24),
      new THREE.MeshBasicMaterial({
        color: 0x3c9aa0,
        wireframe: true,
        transparent: true,
        opacity: 0.22,
      }),
    );
    earth.add(wire);

    const latitudeMaterial = new THREE.LineBasicMaterial({
      color: 0x7bd8ce,
      transparent: true,
      opacity: 0.12,
    });
    for (const latitude of [-60, -30, 0, 30, 60]) {
      const latRad = THREE.MathUtils.degToRad(latitude);
      const r = radius * Math.cos(latRad);
      const y = radius * Math.sin(latRad);
      const points: THREE.Vector3[] = [];
      for (let step = 0; step <= 128; step += 1) {
        const angle = (step / 128) * Math.PI * 2;
        points.push(new THREE.Vector3(Math.cos(angle) * r, y, Math.sin(angle) * r));
      }
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      earth.add(new THREE.Line(geometry, latitudeMaterial));
    }

    const atmosphere = new THREE.Mesh(
      new THREE.SphereGeometry(radius * 1.055, 64, 40),
      new THREE.MeshBasicMaterial({
        color: 0x55d6d0,
        side: THREE.BackSide,
        transparent: true,
        opacity: 0.08,
      }),
    );
    earth.add(atmosphere);

    const nightGlow = new THREE.PointLight(0x9aff6b, 14, 16);
    nightGlow.position.set(-4, 2.4, 5);
    scene.add(nightGlow);
    const coolLight = new THREE.DirectionalLight(0x77cfff, 3.2);
    coolLight.position.set(4, 3, 5);
    scene.add(coolLight);
    scene.add(new THREE.AmbientLight(0x44606b, 2.2));

    const markerGroup = new THREE.Group();
    const markerCore = new THREE.Mesh(
      new THREE.SphereGeometry(0.065, 20, 12),
      new THREE.MeshBasicMaterial({ color: 0xc2ff5d }),
    );
    const markerHalo = new THREE.Mesh(
      new THREE.RingGeometry(0.10, 0.16, 32),
      new THREE.MeshBasicMaterial({
        color: 0xc2ff5d,
        transparent: true,
        opacity: 0.5,
        side: THREE.DoubleSide,
      }),
    );
    markerGroup.add(markerCore, markerHalo);
    earth.add(markerGroup);

    const arcs = new THREE.Group();
    const arcSpecs = [
      [18, -74, 43, 12],
      [22, 90, 35, -97],
      [-15, -48, 20, 77],
      [1, 37, -25, 135],
    ];
    for (const [lat1, lon1, lat2, lon2] of arcSpecs) {
      const a = sphericalPoint(lat1, lon1, radius * 1.015);
      const b = sphericalPoint(lat2, lon2, radius * 1.015);
      const mid = a.clone().add(b).multiplyScalar(0.5).normalize().multiplyScalar(radius * 1.48);
      const curve = new THREE.QuadraticBezierCurve3(a, mid, b);
      const geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(64));
      const material = new THREE.LineBasicMaterial({
        color: 0x82e9d9,
        transparent: true,
        opacity: 0.34,
      });
      arcs.add(new THREE.Line(geometry, material));
    }
    earth.add(arcs);

    const starCount = 380;
    const starPositions = new Float32Array(starCount * 3);
    for (let index = 0; index < starCount; index += 1) {
      const distance = 9 + Math.random() * 10;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      starPositions[index * 3] = distance * Math.sin(phi) * Math.cos(theta);
      starPositions[index * 3 + 1] = distance * Math.cos(phi);
      starPositions[index * 3 + 2] = distance * Math.sin(phi) * Math.sin(theta);
    }
    const starGeometry = new THREE.BufferGeometry();
    starGeometry.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
    scene.add(
      new THREE.Points(
        starGeometry,
        new THREE.PointsMaterial({ color: 0xc8e9e1, size: 0.018, transparent: true, opacity: 0.45 }),
      ),
    );

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let dragging = false;
    let downX = 0;
    let downY = 0;
    let lastX = 0;
    let lastY = 0;

    const setMarker = () => {
      const selected = pointRef.current;
      markerGroup.visible = Boolean(selected);
      if (!selected) return;
      markerGroup.position.copy(sphericalPoint(selected.latitude, selected.longitude, radius * 1.035));
      markerGroup.lookAt(new THREE.Vector3(0, 0, 0));
    };

    const pickFromEvent = (event: PointerEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const intersection = raycaster.intersectObject(globe, false)[0];
      if (!intersection) return;
      const local = earth.worldToLocal(intersection.point.clone()).normalize();
      const latitude = THREE.MathUtils.radToDeg(Math.asin(THREE.MathUtils.clamp(local.y, -1, 1)));
      const longitude = THREE.MathUtils.radToDeg(Math.atan2(local.z, local.x));
      onPickRef.current({
        latitude: Number(latitude.toFixed(5)),
        longitude: Number(longitude.toFixed(5)),
      });
    };

    const onPointerDown = (event: PointerEvent) => {
      dragging = true;
      downX = lastX = event.clientX;
      downY = lastY = event.clientY;
      renderer.domElement.setPointerCapture(event.pointerId);
    };

    const onPointerMove = (event: PointerEvent) => {
      if (!dragging) return;
      const dx = event.clientX - lastX;
      const dy = event.clientY - lastY;
      lastX = event.clientX;
      lastY = event.clientY;
      earth.rotation.y += dx * 0.006;
      earth.rotation.x = THREE.MathUtils.clamp(earth.rotation.x + dy * 0.004, -1.2, 1.2);
    };

    const onPointerUp = (event: PointerEvent) => {
      if (!dragging) return;
      dragging = false;
      const moved = Math.hypot(event.clientX - downX, event.clientY - downY);
      if (moved < 6) pickFromEvent(event);
    };

    renderer.domElement.addEventListener("pointerdown", onPointerDown);
    renderer.domElement.addEventListener("pointermove", onPointerMove);
    renderer.domElement.addEventListener("pointerup", onPointerUp);
    renderer.domElement.style.cursor = "grab";

    const resize = () => {
      const width = Math.max(1, host.clientWidth);
      const height = Math.max(1, host.clientHeight);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();

    let visible = true;
    const visibilityObserver = new IntersectionObserver(([entry]) => {
      visible = entry?.isIntersecting ?? true;
    });
    visibilityObserver.observe(host);

    const clock = new THREE.Clock();
    let raf = 0;
    const render = () => {
      if (visible) {
        const elapsed = clock.getElapsedTime();
        setMarker();
        if (!reducedMotion && !dragging) {
          earth.rotation.y += 0.00065;
          arcs.rotation.y = Math.sin(elapsed * 0.12) * 0.04;
          markerHalo.scale.setScalar(1 + Math.sin(elapsed * 2.2) * 0.22);
          markerHalo.material.opacity = 0.34 + (Math.sin(elapsed * 2.2) + 1) * 0.10;
        }
        renderer.render(scene, camera);
      }
      raf = requestAnimationFrame(render);
    };
    render();

    return () => {
      cancelAnimationFrame(raf);
      observer.disconnect();
      visibilityObserver.disconnect();
      renderer.domElement.removeEventListener("pointerdown", onPointerDown);
      renderer.domElement.removeEventListener("pointermove", onPointerMove);
      renderer.domElement.removeEventListener("pointerup", onPointerUp);
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh || object instanceof THREE.Line || object instanceof THREE.Points) {
          object.geometry?.dispose();
          const material = object.material;
          if (Array.isArray(material)) material.forEach((item) => item.dispose());
          else material?.dispose();
        }
      });
      renderer.dispose();
      if (renderer.domElement.parentElement === host) host.removeChild(renderer.domElement);
    };
  }, []);

  return <div ref={hostRef} className={`world-globe ${className}`.trim()} aria-label="Interactive global field selector" />;
}
