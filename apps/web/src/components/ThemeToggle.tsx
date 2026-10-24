"use client";

import { useEffect, useState } from "react";
import { useT } from "@/lib/i18n";
import { Moon, Sun } from "lucide-react";

type Theme = "dark" | "light";
const STORAGE_KEY = "neyla:theme";

function applyTheme(theme: Theme) {
  document.documentElement.setAttribute("data-theme", theme);
}

export function ThemeToggle() {
  const t = useT();
  const [theme, setTheme] = useState<Theme>("dark");

  // Le script de <head> a déjà appliqué le thème (stocké, sinon préférence
  // système) : on se contente de refléter l'état réel du document.
  useEffect(() => {
    setTheme(document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark");
  }, []);

  function toggle() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* ignore */
    }
  }

  const label = theme === "dark" ? t("theme.light") : t("theme.dark");

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={label}
      title={label}
      className="flex h-9 w-9 items-center justify-center rounded-full text-neutral-300 hover:bg-neutral-800 hover:text-neutral-100"
    >
      {theme === "dark" ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}

function SunIcon() {
  return <Sun size={18} aria-hidden />;
}

function MoonIcon() {
  return <Moon size={18} aria-hidden />;
}
