import { useEffect, useState } from "react";

/**
 * Resolves CSS custom properties to their literal computed values in JS.
 *
 * Needed specifically for SVG gradient <stop> fills: browsers don't
 * reliably inherit CSS custom properties into <stop> elements sitting
 * inside <defs>, since that subtree isn't part of the normal painted
 * render tree that inheritance computation walks — var() silently
 * resolves to nothing there and stop-color falls back to black. Reading
 * the resolved value from document.documentElement (which IS part of the
 * normal tree) and passing a literal color string sidesteps the bug
 * entirely. Reactive to theme changes via a MutationObserver on <html>'s
 * class attribute, since that's the single source of truth applyTheme()
 * writes to (see lib/theme.ts) — this way it stays in sync regardless of
 * which component instance triggered the toggle.
 */
export function useCssVars(names: string[]): Record<string, string> {
  const namesKey = names.join(",");
  const [vars, setVars] = useState<Record<string, string>>({});

  useEffect(() => {
    const read = () => {
      const style = getComputedStyle(document.documentElement);
      const next: Record<string, string> = {};
      for (const name of names) {
        next[name] = style.getPropertyValue(name).trim();
      }
      setVars(next);
    };

    read();
    const observer = new MutationObserver(read);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [namesKey]);

  return vars;
}
