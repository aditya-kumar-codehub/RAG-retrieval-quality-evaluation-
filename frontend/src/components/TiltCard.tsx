import type { ReactNode, MouseEvent } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";

// Cursor-tracking 3D tilt for genuinely clickable card-links — Vercel/
// Linear-style depth. Scoped intentionally: only apply this to elements
// that ARE a link/button, since the tilt signals "hover me, I'm
// interactive" — putting it on a static display card would be a false
// affordance.
const MAX_TILT_DEG = 8;

export function TiltCard({ children, className }: { children: ReactNode; className?: string }) {
  const x = useMotionValue(0.5);
  const y = useMotionValue(0.5);
  const springConfig = { stiffness: 300, damping: 28, mass: 0.5 };
  const rotateX = useSpring(useTransform(y, [0, 1], [MAX_TILT_DEG, -MAX_TILT_DEG]), springConfig);
  const rotateY = useSpring(useTransform(x, [0, 1], [-MAX_TILT_DEG, MAX_TILT_DEG]), springConfig);
  const glowX = useTransform(x, [0, 1], ["0%", "100%"]);
  const glowY = useTransform(y, [0, 1], ["0%", "100%"]);

  function handleMouseMove(e: MouseEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    x.set((e.clientX - rect.left) / rect.width);
    y.set((e.clientY - rect.top) / rect.height);
  }

  function handleMouseLeave() {
    x.set(0.5);
    y.set(0.5);
  }

  return (
    <div style={{ perspective: 900 }} className={className}>
      <motion.div
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
        whileHover={{ scale: 1.015 }}
        transition={{ scale: { duration: 0.2, ease: "easeOut" } }}
        className="group relative h-full"
      >
        {/* A soft light that leans toward the cursor position, reinforcing the tilt's sense of depth. */}
        <motion.div
          aria-hidden
          className="pointer-events-none absolute inset-0 z-10 rounded-[var(--radius-lg)] opacity-0 transition-opacity duration-200 group-hover:opacity-100"
          style={{
            background: useTransform(
              [glowX, glowY],
              ([gx, gy]) => `radial-gradient(circle at ${gx} ${gy}, color-mix(in oklab, var(--accent) 16%, transparent), transparent 60%)`,
            ),
          }}
        />
        {children}
      </motion.div>
    </div>
  );
}
