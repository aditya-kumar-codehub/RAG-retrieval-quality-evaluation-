import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { fadeInUp } from "@/lib/motion";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeInUp}
      className="mb-7 flex flex-col justify-between gap-4 sm:mb-9 sm:flex-row sm:items-end"
    >
      <div>
        {eyebrow && (
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-accent">{eyebrow}</p>
        )}
        <h1 className="font-display text-[30px] font-semibold leading-[1.1] tracking-[-0.02em] text-text-primary sm:text-[38px]">
          {title}
        </h1>
        {description && (
          <p className="mt-2.5 max-w-2xl text-[14.5px] leading-relaxed text-text-secondary">{description}</p>
        )}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </motion.div>
  );
}
