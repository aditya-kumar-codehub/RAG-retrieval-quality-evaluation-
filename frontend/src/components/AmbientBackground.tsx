import { useEffect, useRef } from "react";

interface Particle {
  x: number;
  y: number;
  r: number;
  vx: number;
  vy: number;
  alpha: number;
}

/**
 * App-wide ambient background: a slow-drifting dark gradient wash (pure
 * CSS, see .ambient-bg-gradient in index.css) plus a light canvas particle
 * field. Mounted once in AppShell so it persists across route changes
 * instead of resetting on every page nav. Deliberately restrained — this
 * sits behind real content (cards, tables, charts) on every page, so it
 * has to stay a "barely there" atmosphere, not a wallpaper.
 */
export function AmbientBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    let width = 0;
    let height = 0;
    let particles: Particle[] = [];
    let raf = 0;

    function initParticles() {
      // Density-based count, capped — stays cheap on large/ultrawide monitors.
      const count = Math.min(55, Math.floor((width * height) / 26000));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        r: Math.random() * 1.5 + 0.5,
        vx: (Math.random() - 0.5) * 0.05,
        vy: (Math.random() - 0.5) * 0.05,
        alpha: Math.random() * 0.3 + 0.12,
      }));
    }

    function resize() {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas!.width = width * dpr;
      canvas!.height = height * dpr;
      canvas!.style.width = `${width}px`;
      canvas!.style.height = `${height}px`;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      initParticles();
    }

    function draw() {
      ctx!.clearRect(0, 0, width, height);
      const isDark = document.documentElement.classList.contains("dark");
      const dotColor = isDark ? "255,255,255" : "15,23,34";
      for (const p of particles) {
        ctx!.beginPath();
        ctx!.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx!.fillStyle = `rgba(${dotColor},${p.alpha})`;
        ctx!.fill();

        if (!prefersReducedMotion) {
          p.x += p.vx;
          p.y += p.vy;
          if (p.x < -10) p.x = width + 10;
          else if (p.x > width + 10) p.x = -10;
          if (p.y < -10) p.y = height + 10;
          else if (p.y > height + 10) p.y = -10;
        }
      }
    }

    let lastFrame = 0;
    function loop(time: number) {
      // ~30fps is plenty for dots this slow — cheaper than a full 60fps loop.
      if (time - lastFrame > 33) {
        draw();
        lastFrame = time;
      }
      raf = requestAnimationFrame(loop);
    }

    function handleVisibility() {
      if (document.hidden) {
        cancelAnimationFrame(raf);
      } else if (!prefersReducedMotion) {
        raf = requestAnimationFrame(loop);
      }
    }

    resize();
    window.addEventListener("resize", resize);
    document.addEventListener("visibilitychange", handleVisibility);

    if (prefersReducedMotion) {
      draw(); // single static frame, no rAF loop at all
    } else {
      raf = requestAnimationFrame(loop);
    }

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, []);

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 z-0 overflow-hidden bg-background">
      <div className="ambient-bg-gradient absolute inset-[-15%]" />
      <canvas ref={canvasRef} className="absolute inset-0" />
    </div>
  );
}
