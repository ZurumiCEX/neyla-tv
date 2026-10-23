"use client";

// Utilitaires communs aux widgets OBS (/overlay/<token>/…).

import { useEffect } from "react";

const PUBLIC_API = process.env.NEXT_PUBLIC_API_URL ?? "";

export function wsBase(): string {
  if (PUBLIC_API) return PUBLIC_API.replace(/^http/, "ws");
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${window.location.host}`;
  }
  return "";
}

export type OverlayInfo = {
  slug: string;
  is_live: boolean;
  goal: { title: string; kind: "subs" | "tips"; target: number; current: number } | null;
};

/** Fond transparent pour la capture « Source navigateur » d'OBS. */
export function useTransparentBody(): void {
  useEffect(() => {
    const prev = document.body.style.background;
    document.body.style.background = "transparent";
    return () => {
      document.body.style.background = prev;
    };
  }, []);
}
