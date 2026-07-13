import type { Transition, Variants } from "framer-motion";

// Shared Framer Motion variants so entrance/hover motion is consistent
// across pages instead of hand-tuned per file. Keep durations short and
// easing gentle — the goal is "purposeful," not "look at me."

export const EASE_OUT: Transition["ease"] = [0.16, 1, 0.3, 1];

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: EASE_OUT } },
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.3, ease: EASE_OUT } },
};

export const staggerContainer: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.06, delayChildren: 0.02 },
  },
};

// Spread onto a motion.div for a subtle lift on hover — used by
// Card's `interactive` prop and other clickable surfaces.
export const hoverLift = {
  whileHover: { y: -3, transition: { duration: 0.18, ease: EASE_OUT } },
  whileTap: { y: 0, scale: 0.99 },
};

export const tapScale = {
  whileTap: { scale: 0.97 },
};
