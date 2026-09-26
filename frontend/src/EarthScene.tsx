import { useEffect, useRef } from "react";
import * as THREE from "three";

type Props = {
  className?: string;
  accent?: "green" | "cyan";
};

export default function EarthScene({ className = "", accent = "green" }: Props) {
  const hostRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const width = host.clientWidth || 640;
    const height = host.clientHeight || 640;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
    camera.position.set(0, 0, 5.4);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "high-performance" });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.8));
    renderer.setSize(width, height);
    renderer.setClearColor(0x000000, 0);
    host.appendChild(renderer.domElement);

    const root = new THREE.Group();
    scene.add(root);

    const isCyan = accent === "cyan";
    const baseColor = new THREE.Color(isCyan ? 0x65f4ff : 0x9ef2a6);
    const darkColor = new THREE.Color(isCyan ? 0x123f4a : 0x153a23);

    const globe = new THREE.Mesh(
      new THREE.IcosahedronGeometry(1.48, 5),
      new THREE.MeshPhysicalMaterial({
        color: darkColor,
        roughness: 0.78,
        metalness: 0.08,
        transparent: true,
        opacity: 0.76,
        clearcoat: 0.2,
      }),
    );
    root.add(globe);

    const wire = new THREE.Mesh(
      new THREE.IcosahedronGeometry(1.505, 3),
      new THREE.MeshBasicMaterial({
        color: baseColor,
        transparent: true,
        opacity: 0.18,
        wireframe: true,
      }),
    );
    root.add(wire);

    const pointGeometry = new THREE.BufferGeometry();
    const pointCount = 900;
    const positions = new Float32Array(pointCount * 3);
    for (let i = 0; i < pointCount; i += 1) {
      const u = Math.random();
      const v = Math.random();
      const theta = 2 * Math.PI * u;
      const phi = Math.acos(2 * v - 1);
      const radius = 1.56 + Math.random() * 0.035;
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.cos(phi);
      positions[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
    }
    pointGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const points = new THREE.Points(
      pointGeometry,
      new THREE.PointsMaterial({
        color: baseColor,
        size: 0.018,
        transparent: true,
        opacity: 0.62,
      }),
    );
    root.add(points);

    const ringGroup = new THREE.Group();
    [
      [1.92, 0.02, 0.12],
      [2.15, 0.012, -0.27],
      [2.42, 0.008, 0.38],
    ].forEach(([radius, tube, tilt], index) => {
      const torus = new THREE.Mesh(
        new THREE.TorusGeometry(radius, tube, 10, 180),
        new THREE.MeshBasicMaterial({
          color: index === 1 ? 0xffffff : baseColor,
          transparent: true,
          opacity: index === 1 ? 0.1 : 0.24,
        }),
      );
      torus.rotation.x = Math.PI / 2 + tilt;
      torus.rotation.y = index * 0.45;
      ringGroup.add(torus);
    });
    root.add(ringGroup);

    const marker = new THREE.Mesh(
      new THREE.SphereGeometry(0.055, 20, 20),
      new THREE.MeshBasicMaterial({ color: 0xff5d46 }),
    );
    marker.position.set(0.52, 0.35, 1.44);
    root.add(marker);

    const markerHalo = new THREE.Mesh(
      new THREE.RingGeometry(0.09, 0.16, 48),
      new THREE.MeshBasicMaterial({
        color: 0xff8b72,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.5,
      }),
    );
    markerHalo.position.copy(marker.position);
    markerHalo.lookAt(camera.position);
    root.add(markerHalo);

    const satellite = new THREE.Group();
    const body = new THREE.Mesh(
      new THREE.BoxGeometry(0.2, 0.12, 0.1),
      new THREE.MeshStandardMaterial({ color: 0xe8f6ea, metalness: 0.4, roughness: 0.3 }),
    );
    const wingMaterial = new THREE.MeshStandardMaterial({ color: 0x4f8ea1, metalness: 0.25, roughness: 0.45 });
    const leftWing = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.04, 0.14), wingMaterial);
    leftWing.position.x = -0.28;
    const rightWing = leftWing.clone();
    rightWing.position.x = 0.28;
    satellite.add(body, leftWing, rightWing);
    satellite.scale.setScalar(0.75);
    root.add(satellite);

    const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
    keyLight.position.set(3, 2.6, 4);
    scene.add(keyLight);
    const fillLight = new THREE.PointLight(baseColor, 1.4, 8);
    fillLight.position.set(-2.5, -1.2, 2.6);
    scene.add(fillLight);
    scene.add(new THREE.AmbientLight(0xffffff, 0.3));

    const starGeometry = new THREE.BufferGeometry();
    const starCount = 260;
    const starPositions = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount; i += 1) {
      starPositions[i * 3] = (Math.random() - 0.5) * 10;
      starPositions[i * 3 + 1] = (Math.random() - 0.5) * 7;
      starPositions[i * 3 + 2] = -1.5 - Math.random() * 6;
    }
    starGeometry.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
    const stars = new THREE.Points(
      starGeometry,
      new THREE.PointsMaterial({ color: 0xffffff, size: 0.018, transparent: true, opacity: 0.35 }),
    );
    scene.add(stars);

    let pointerX = 0;
    let pointerY = 0;
    const onPointerMove = (event: PointerEvent) => {
      const rect = host.getBoundingClientRect();
      pointerX = ((event.clientX - rect.left) / rect.width - 0.5) * 0.4;
      pointerY = ((event.clientY - rect.top) / rect.height - 0.5) * 0.25;
    };
    host.addEventListener("pointermove", onPointerMove);

    const clock = new THREE.Clock();
    let raf = 0;

    const render = () => {
      const elapsed = clock.getElapsedTime();
      if (!reducedMotion) {
        root.rotation.y = elapsed * 0.11 + pointerX;
        root.rotation.x = -0.08 + pointerY;
        wire.rotation.y = -elapsed * 0.03;
        ringGroup.rotation.z = elapsed * 0.055;
        const orbit = elapsed * 0.42;
        satellite.position.set(Math.cos(orbit) * 2.15, Math.sin(orbit * 0.7) * 0.75, Math.sin(orbit) * 0.65);
        satellite.rotation.z = orbit + 1.1;
        markerHalo.scale.setScalar(1 + Math.sin(elapsed * 2.5) * 0.16);
        markerHalo.material.opacity = 0.32 + (Math.sin(elapsed * 2.5) + 1) * 0.1;
      }
      renderer.render(scene, camera);
      raf = requestAnimationFrame(render);
    };
    render();

    const resize = () => {
      const nextWidth = host.clientWidth || width;
      const nextHeight = host.clientHeight || height;
      camera.aspect = nextWidth / nextHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(nextWidth, nextHeight);
    };
    const observer = new ResizeObserver(resize);
    observer.observe(host);

    return () => {
      cancelAnimationFrame(raf);
      observer.disconnect();
      host.removeEventListener("pointermove", onPointerMove);
      renderer.dispose();
      pointGeometry.dispose();
      starGeometry.dispose();
      host.removeChild(renderer.domElement);
    };
  }, [accent]);

  return <div ref={hostRef} className={`earth-scene ${className}`} aria-hidden="true" />;
}
