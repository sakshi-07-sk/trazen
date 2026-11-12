"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";

interface NodeSpec {
  pos: [number, number, number];
  color: number;
  size: number;
}

const GRAPH_NODES: NodeSpec[] = [
  { pos: [-3.4, 0.8, 0.4], color: 0xef4444, size: 0.22 }, // Suspect origin
  { pos: [-1.7, 1.5, -0.6], color: 0x00e5ff, size: 0.15 },
  { pos: [-1.4, -0.8, 0.9], color: 0xf97316, size: 0.17 },
  { pos: [0.0, 0.4, 0.0], color: 0x00e5ff, size: 0.2 }, // Central hub
  { pos: [0.4, 1.9, 0.8], color: 0x00e5ff, size: 0.14 },
  { pos: [0.6, -1.6, -0.7], color: 0xf59e0b, size: 0.15 },
  { pos: [2.0, 1.1, -0.3], color: 0x00e5ff, size: 0.16 },
  { pos: [2.2, -0.6, 0.9], color: 0x00e5ff, size: 0.15 },
  { pos: [3.6, 0.2, -0.2], color: 0x22c55e, size: 0.21 }, // Probable receiver / exit
  { pos: [3.3, -1.5, -0.9], color: 0xf97316, size: 0.16 },
  { pos: [-0.4, 2.3, -1.3], color: 0x8a929e, size: 0.11 },
  { pos: [1.4, 2.2, 1.1], color: 0x00e5ff, size: 0.12 },
];

const GRAPH_EDGES: [number, number][] = [
  [0, 1],
  [0, 2],
  [1, 3],
  [2, 3],
  [1, 4],
  [2, 5],
  [3, 6],
  [3, 7],
  [4, 6],
  [5, 7],
  [6, 8],
  [7, 8],
  [7, 9],
  [4, 10],
  [6, 11],
];

export function HeroGraph3D() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [fallback, setFallback] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
    } catch {
      setFallback(true);
      return;
    }

    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(48, width / height, 0.1, 100);
    camera.position.set(0, 0.2, 8.2);

    const group = new THREE.Group();
    scene.add(group);

    // Subtle background star/ledger dust
    const dustCount = 220;
    const dustPositions = new Float32Array(dustCount * 3);
    for (let i = 0; i < dustCount; i++) {
      dustPositions[i * 3] = (Math.random() - 0.5) * 18;
      dustPositions[i * 3 + 1] = (Math.random() - 0.5) * 10;
      dustPositions[i * 3 + 2] = (Math.random() - 0.5) * 8 - 2;
    }
    const dustGeo = new THREE.BufferGeometry();
    dustGeo.setAttribute("position", new THREE.BufferAttribute(dustPositions, 3));
    const dustMat = new THREE.PointsMaterial({
      color: 0x00e5ff,
      size: 0.03,
      transparent: true,
      opacity: 0.28,
    });
    const dust = new THREE.Points(dustGeo, dustMat);
    scene.add(dust);

    // Build nodes + outer halos
    const nodeMeshes: THREE.Mesh[] = [];
    const sphereGeo = new THREE.SphereGeometry(1, 20, 20);
    const ringGeo = new THREE.RingGeometry(1.4, 1.65, 32);

    GRAPH_NODES.forEach((n) => {
      const mat = new THREE.MeshBasicMaterial({ color: n.color });
      const mesh = new THREE.Mesh(sphereGeo, mat);
      mesh.position.set(...n.pos);
      mesh.scale.setScalar(n.size);
      group.add(mesh);
      nodeMeshes.push(mesh);

      const haloMat = new THREE.MeshBasicMaterial({
        color: n.color,
        transparent: true,
        opacity: 0.22,
        side: THREE.DoubleSide,
      });
      const halo = new THREE.Mesh(ringGeo, haloMat);
      halo.position.set(...n.pos);
      halo.scale.setScalar(n.size);
      group.add(halo);
    });

    // Build edges + flowing trace pulses
    const pulseSpecs: {
      start: THREE.Vector3;
      end: THREE.Vector3;
      offset: number;
      speed: number;
      mesh: THREE.Mesh;
    }[] = [];

    const pulseGeo = new THREE.SphereGeometry(0.045, 10, 10);
    const pulseMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff });

    GRAPH_EDGES.forEach(([a, b], idx) => {
      const start = new THREE.Vector3(...GRAPH_NODES[a].pos);
      const end = new THREE.Vector3(...GRAPH_NODES[b].pos);
      const lineGeo = new THREE.BufferGeometry().setFromPoints([start, end]);
      const lineMat = new THREE.LineBasicMaterial({
        color: idx % 3 === 0 ? 0x00e5ff : 0x3b4758,
        transparent: true,
        opacity: idx % 3 === 0 ? 0.5 : 0.35,
      });
      const line = new THREE.Line(lineGeo, lineMat);
      group.add(line);

      const pulseMesh = new THREE.Mesh(pulseGeo, pulseMat);
      group.add(pulseMesh);
      pulseSpecs.push({
        start,
        end,
        offset: (idx * 0.17) % 1,
        speed: 0.28 + (idx % 4) * 0.07,
        mesh: pulseMesh,
      });
    });

    let targetRotX = 0;
    let targetRotY = 0;

    const handlePointerMove = (e: PointerEvent) => {
      const nx = (e.clientX / window.innerWidth) * 2 - 1;
      const ny = (e.clientY / window.innerHeight) * 2 - 1;
      targetRotY = nx * 0.28;
      targetRotX = -ny * 0.18;
    };

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth || window.innerWidth;
      const h = container.clientHeight || window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("resize", handleResize);

    let rafId = 0;
    const clock = new THREE.Clock();

    const animate = () => {
      const elapsed = clock.getElapsedTime();

      if (!prefersReduced) {
        group.rotation.y += (targetRotY - group.rotation.y) * 0.04 + 0.0008;
        group.rotation.x += (targetRotX - group.rotation.x) * 0.04;
        dust.rotation.y = elapsed * 0.015;

        pulseSpecs.forEach((p) => {
          const t = (elapsed * p.speed + p.offset) % 1;
          p.mesh.position.lerpVectors(p.start, p.end, t);
        });
      } else {
        pulseSpecs.forEach((p) => {
          p.mesh.position.lerpVectors(p.start, p.end, 0.5);
        });
      }

      renderer.render(scene, camera);
      if (!prefersReduced) {
        rafId = requestAnimationFrame(animate);
      }
    };

    animate();

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("resize", handleResize);
      sphereGeo.dispose();
      ringGeo.dispose();
      pulseGeo.dispose();
      dustGeo.dispose();
      dustMat.dispose();
      pulseMat.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  if (fallback) {
    return (
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_60%_40%,rgba(0,229,255,0.12),transparent_55%)]" />
    );
  }

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
      aria-hidden="true"
    />
  );
}
