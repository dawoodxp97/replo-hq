"use client";

import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

export type ThemeMode = "light" | "dark" | "system";

interface ThemeContextValue {
  theme: ThemeMode;
  setTheme: (next: ThemeMode) => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const STORAGE_KEY = "theme";

function getStoredTheme(): ThemeMode | null {
  try {
    const raw = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (!raw) return null;
    if (raw === "light" || raw === "dark" || raw === "system") return raw;
    return null;
  } catch {
    return null;
  }
}

function applyDarkClass(shouldDark: boolean) {
  if (typeof document === "undefined") return;
  const root = document.documentElement; // html
  if (shouldDark) {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeMode>(() => getStoredTheme() ?? "system");

  // Track system preference
  const media = useMemo(() =>
    typeof window !== "undefined" ? window.matchMedia("(prefers-color-scheme: dark)") : undefined,
    []
  );

  const [systemDark, setSystemDark] = useState<boolean>(() => media?.matches ?? false);

  // Listen to system preference changes
  useEffect(() => {
    if (!media) return;
    const handler = (e: MediaQueryListEvent) => setSystemDark(e.matches);
    // Wrap to satisfy EventListener typing
    const listener: EventListener = (e) => handler(e as MediaQueryListEvent);

    // Modern browsers
    if (typeof media.addEventListener === "function") {
      media.addEventListener("change", listener);
    }

    // Older Safari fallback
    const legacy = media as unknown as {
      addListener?: (cb: (ev: MediaQueryListEvent) => void) => void;
      removeListener?: (cb: (ev: MediaQueryListEvent) => void) => void;
    };
    if (typeof legacy.addListener === "function") {
      legacy.addListener(handler);
    }

    return () => {
      if (typeof media.removeEventListener === "function") {
        media.removeEventListener("change", listener);
      }
      if (typeof legacy.removeListener === "function") {
        legacy.removeListener(handler);
      }
    };
  }, [media]);

  // Apply theme and persist
  useEffect(() => {
    const effectiveDark = theme === "dark" || (theme === "system" && systemDark);
    applyDarkClass(effectiveDark);
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch {}
  }, [theme, systemDark]);

  const setTheme = (next: ThemeMode) => setThemeState(next);

  const value: ThemeContextValue = {
    theme,
    setTheme,
    isDark: theme === "dark" || (theme === "system" && systemDark),
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}