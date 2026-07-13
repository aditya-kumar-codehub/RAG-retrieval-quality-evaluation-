import { useEffect, useState } from "react";

export type Theme = "light" | "dark";
const STORAGE_KEY = "rag-eval-theme";

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark");
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
    // Dark-first by default (matches Linear/Vercel/Raycast/Stripe dashboard),
    // rather than following OS preference — still fully overridable via the toggle.
    return stored ?? "dark";
  });

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const setTheme = (next: Theme) => {
    localStorage.setItem(STORAGE_KEY, next);
    setThemeState(next);
  };

  return { theme, toggleTheme: () => setTheme(theme === "dark" ? "light" : "dark") };
}
