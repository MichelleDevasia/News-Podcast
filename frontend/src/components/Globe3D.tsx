import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import './Globe3D.css';

interface Globe3DProps {
  theme: 'dark' | 'light';
  size?: number;
}

/**
 * Generates a high-definition equirectangular Earth texture locally on a canvas.
 * Completely self-contained: no external image dependencies or network vulnerabilities.
 */
function createEarthCanvasTexture(theme: 'dark' | 'light'): THREE.CanvasTexture {
  const width = 2048;
  const height = 1024;
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d')!;

  const isDark = theme === 'dark';

  // 1. Ocean background with subtle gradient
  const oceanGrad = ctx.createLinearGradient(0, 0, 0, height);
  if (isDark) {
    oceanGrad.addColorStop(0, '#06172d');
    oceanGrad.addColorStop(0.5, '#071d3a');
    oceanGrad.addColorStop(1, '#051428');
  } else {
    oceanGrad.addColorStop(0, '#dbeafe');
    oceanGrad.addColorStop(0.5, '#e0f2fe');
    oceanGrad.addColorStop(1, '#bae6fd');
  }
  ctx.fillStyle = oceanGrad;
  ctx.fillRect(0, 0, width, height);

  // 2. Latitudinal & Longitudinal grid lines
  ctx.strokeStyle = isDark ? 'rgba(56, 189, 248, 0.12)' : 'rgba(2, 132, 199, 0.15)';
  ctx.lineWidth = 1.5;

  // Parallels (latitude)
  for (let lat = -80; lat <= 80; lat += 20) {
    const y = ((90 - lat) / 180) * height;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }

  // Meridians (longitude)
  for (let lon = -180; lon <= 180; lon += 30) {
    const x = ((lon + 180) / 360) * width;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }

  // Equator
  ctx.strokeStyle = isDark ? 'rgba(56, 189, 248, 0.25)' : 'rgba(2, 132, 199, 0.3)';
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.moveTo(0, height / 2);
  ctx.lineTo(width, height / 2);
  ctx.stroke();

  // 3. Render Landmasses
  ctx.fillStyle = isDark ? '#1d4ed8' : '#0284c7';
  ctx.strokeStyle = isDark ? '#3b82f6' : '#0369a1';
  ctx.lineWidth = 2;

  // Helper to draw normalized equirectangular polygon
  const drawPolygon = (points: [number, number][]) => {
    ctx.beginPath();
    points.forEach(([lon, lat], i) => {
      const x = ((lon + 180) / 360) * width;
      const y = ((90 - lat) / 180) * height;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  };

  // North America
  drawPolygon([
    [-165, 65], [-140, 70], [-100, 72], [-80, 70], [-60, 60],
    [-65, 45], [-75, 35], [-80, 25], [-95, 20], [-105, 20],
    [-120, 35], [-125, 50], [-160, 58], [-165, 65]
  ]);

  // Central America
  drawPolygon([
    [-105, 20], [-85, 20], [-78, 8], [-85, 12], [-100, 16], [-105, 20]
  ]);

  // South America
  drawPolygon([
    [-78, 12], [-50, -5], [-35, -7], [-40, -22], [-55, -35],
    [-68, -55], [-75, -45], [-72, -30], [-80, -5], [-78, 12]
  ]);

  // Greenland
  drawPolygon([
    [-55, 60], [-20, 65], [-25, 82], [-50, 82], [-55, 60]
  ]);

  // Europe & Scandinavia
  drawPolygon([
    [-10, 36], [0, 42], [15, 40], [25, 38], [30, 45],
    [25, 55], [30, 65], [15, 70], [5, 60], [-5, 50], [-10, 36]
  ]);

  // Africa
  drawPolygon([
    [-17, 15], [-5, 35], [12, 37], [32, 32], [50, 12],
    [42, -10], [30, -32], [18, -34], [12, -15], [0, 5], [-17, 15]
  ]);

  // Asia
  drawPolygon([
    [32, 32], [45, 42], [60, 40], [75, 42], [105, 38],
    [130, 45], [140, 55], [170, 65], [180, 70], [130, 75],
    [80, 72], [50, 65], [35, 50], [32, 32]
  ]);

  // Indian Subcontinent
  drawPolygon([
    [68, 24], [78, 30], [90, 24], [84, 15], [80, 8], [74, 14], [68, 24]
  ]);

  // Southeast Asia
  drawPolygon([
    [98, 20], [110, 20], [108, 10], [102, 5], [98, 10], [98, 20]
  ]);

  // Australia
  drawPolygon([
    [114, -22], [130, -12], [142, -12], [152, -28], [148, -38],
    [135, -36], [115, -32], [114, -22]
  ]);

  // Antarctica
  drawPolygon([
    [-180, -78], [-120, -74], [-60, -70], [0, -68],
    [60, -70], [120, -74], [180, -78], [180, -90], [-180, -90]
  ]);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

// Convert geographic lat/lon to 3D Cartesian coordinates on sphere
function latLonToVector3(lat: number, lon: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);
  return new THREE.Vector3(x, y, z);
}

export const Globe3D: React.FC<Globe3DProps> = ({ theme }) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // Check prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Scene Setup
    const scene = new THREE.Scene();

    const width = container.clientWidth || 460;
    const height = container.clientHeight || 460;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 4.4;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Root Globe Group (tilted at Earth's 23.5° axial tilt)
    const earthGroup = new THREE.Group();
    earthGroup.rotation.z = (23.5 * Math.PI) / 180;
    scene.add(earthGroup);

    // Lights
    const ambientLight = new THREE.AmbientLight(
      theme === 'dark' ? 0x223355 : 0x88aacc,
      theme === 'dark' ? 1.4 : 1.8
    );
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, theme === 'dark' ? 2.2 : 2.5);
    sunLight.position.set(5, 3, 4);
    scene.add(sunLight);

    const fillLight = new THREE.DirectionalLight(
      theme === 'dark' ? 0x38bdf8 : 0x0284c7,
      theme === 'dark' ? 0.8 : 0.6
    );
    fillLight.position.set(-5, -2, -3);
    scene.add(fillLight);

    // Earth Sphere Geometry & Material
    const radius = 1.45;
    const sphereGeometry = new THREE.SphereGeometry(radius, 64, 64);
    const earthTexture = createEarthCanvasTexture(theme);

    const sphereMaterial = new THREE.MeshPhongMaterial({
      map: earthTexture,
      shininess: theme === 'dark' ? 24 : 14,
      specular: theme === 'dark' ? new THREE.Color(0x2266aa) : new THREE.Color(0x4488bb),
    });

    const earthMesh = new THREE.Mesh(sphereGeometry, sphereMaterial);
    earthGroup.add(earthMesh);

    // Atmospheric Glow Shell
    const atmosphereGeometry = new THREE.SphereGeometry(radius * 1.025, 48, 48);
    const atmosphereMaterial = new THREE.MeshBasicMaterial({
      color: theme === 'dark' ? 0x38bdf8 : 0x0284c7,
      transparent: true,
      opacity: theme === 'dark' ? 0.18 : 0.12,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
    });
    const atmosphereMesh = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
    earthGroup.add(atmosphereMesh);

    // Global News Hub Beacon Nodes (New York, London, New Delhi, Tokyo)
    const beaconsData = [
      { name: 'New York', lat: 40.71, lon: -74.0 },
      { name: 'London', lat: 51.5, lon: -0.12 },
      { name: 'New Delhi', lat: 28.61, lon: 77.2 },
      { name: 'Tokyo', lat: 35.67, lon: 139.65 },
    ];

    const beaconGroup = new THREE.Group();
    const beaconGeometry = new THREE.SphereGeometry(0.038, 16, 16);
    const beaconMaterial = new THREE.MeshBasicMaterial({
      color: 0xef4444,
      transparent: true,
      opacity: 0.95,
    });

    beaconsData.forEach((b) => {
      const pos = latLonToVector3(b.lat, b.lon, radius * 1.008);
      const beaconMesh = new THREE.Mesh(beaconGeometry, beaconMaterial);
      beaconMesh.position.copy(pos);
      beaconGroup.add(beaconMesh);
    });
    earthGroup.add(beaconGroup);

    // --- 3D Orbital Paths & Revolving Satellites ---
    const orbitGroup = new THREE.Group();
    scene.add(orbitGroup);

    // Function to build 3D elliptical orbit curve
    const buildOrbit = (a: number, b: number, rotX: number, rotY: number, rotZ: number) => {
      const points: THREE.Vector3[] = [];
      const segments = 120;
      for (let i = 0; i <= segments; i++) {
        const theta = (i / segments) * Math.PI * 2;
        points.push(new THREE.Vector3(a * Math.cos(theta), b * Math.sin(theta), 0));
      }
      const geom = new THREE.BufferGeometry().setFromPoints(points);
      const mat = new THREE.LineDashedMaterial({
        color: theme === 'dark' ? 0x38bdf8 : 0x0284c7,
        transparent: true,
        opacity: theme === 'dark' ? 0.45 : 0.4,
        dashSize: 0.1,
        gapSize: 0.06,
        linewidth: 1,
      });
      const line = new THREE.LineLoop(geom, mat);
      line.computeLineDistances();
      line.rotation.set(rotX, rotY, rotZ);
      return { line, a, b, rotX, rotY, rotZ };
    };

    const orbit1 = buildOrbit(2.1, 1.25, Math.PI / 4, Math.PI / 6, 0);
    const orbit2 = buildOrbit(2.0, 1.15, -Math.PI / 3, -Math.PI / 8, Math.PI / 4);
    orbitGroup.add(orbit1.line);
    orbitGroup.add(orbit2.line);

    // Satellite Markers moving on orbits
    const satMaterial1 = new THREE.MeshBasicMaterial({
      color: theme === 'dark' ? 0x38bdf8 : 0x0284c7,
    });
    const satMaterial2 = new THREE.MeshBasicMaterial({
      color: 0xef4444,
    });
    const sat1 = new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 16), satMaterial1);
    const sat2 = new THREE.Mesh(new THREE.SphereGeometry(0.04, 16, 16), satMaterial2);
    orbitGroup.add(sat1);
    orbitGroup.add(sat2);

    // Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const elapsed = clock.getElapsedTime();

      // Slow axial rotation
      if (!prefersReducedMotion) {
        earthGroup.rotation.y += 0.0022;
      }

      // Orbital Satellites Motion in 3D
      const theta1 = elapsed * 0.45;
      const v1 = new THREE.Vector3(
        orbit1.a * Math.cos(theta1),
        orbit1.b * Math.sin(theta1),
        0
      );
      v1.applyEuler(new THREE.Euler(orbit1.rotX, orbit1.rotY, orbit1.rotZ));
      sat1.position.copy(v1);

      const theta2 = -elapsed * 0.38;
      const v2 = new THREE.Vector3(
        orbit2.a * Math.cos(theta2),
        orbit2.b * Math.sin(theta2),
        0
      );
      v2.applyEuler(new THREE.Euler(orbit2.rotX, orbit2.rotY, orbit2.rotZ));
      sat2.position.copy(v2);

      // Beacon subtle pulse
      const pulseScale = 1.0 + 0.25 * Math.sin(elapsed * 3.5);
      beaconGroup.scale.set(pulseScale, pulseScale, pulseScale);

      renderer.render(scene, camera);
    };

    animate();

    // Resize Observer
    const resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const { width: newWidth, height: newHeight } = entry.contentRect;
        if (newWidth > 0 && newHeight > 0) {
          camera.aspect = newWidth / newHeight;
          camera.updateProjectionMatrix();
          renderer.setSize(newWidth, newHeight);
        }
      }
    });
    resizeObserver.observe(container);

    // Cleanup resources
    return () => {
      cancelAnimationFrame(animationFrameId);
      resizeObserver.disconnect();
      sphereGeometry.dispose();
      sphereMaterial.dispose();
      earthTexture.dispose();
      atmosphereGeometry.dispose();
      atmosphereMaterial.dispose();
      beaconGeometry.dispose();
      beaconMaterial.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [theme]);

  return (
    <div className={`globe-3d-wrapper ${theme}`} aria-label="Genuinely 3D WebGL Earth visualization">
      {/* Category Indicators overlaid in 3D space */}
      <div className="cat-tag-3d tag-tech">
        <span className="cat-dot-3d dot-tech"></span>
        <span className="cat-text-3d">Technology</span>
      </div>

      <div className="cat-tag-3d tag-world">
        <span className="cat-dot-3d dot-world"></span>
        <span className="cat-text-3d">World</span>
      </div>

      <div className="cat-tag-3d tag-business">
        <span className="cat-dot-3d dot-biz"></span>
        <span className="cat-text-3d">Business</span>
      </div>

      <div className="cat-tag-3d tag-health">
        <span className="cat-dot-3d dot-health"></span>
        <span className="cat-text-3d">Health</span>
      </div>

      {/* Three.js Canvas Container */}
      <div ref={mountRef} className="globe-3d-canvas-container" />
    </div>
  );
};
