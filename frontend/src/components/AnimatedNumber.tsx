import { useEffect } from "react";
import { animate, motion, useMotionValue, useTransform } from "framer-motion";

export function AnimatedNumber({
  value,
  format = (n) => Math.round(n).toString(),
  duration = 1,
}: {
  value: number;
  format?: (n: number) => string;
  duration?: number;
}) {
  const motionValue = useMotionValue(0);
  const display = useTransform(motionValue, format);

  useEffect(() => {
    const controls = animate(motionValue, value, { duration, ease: [0.16, 1, 0.3, 1] });
    return controls.stop;
  }, [value, duration, motionValue]);

  return <motion.span>{display}</motion.span>;
}
