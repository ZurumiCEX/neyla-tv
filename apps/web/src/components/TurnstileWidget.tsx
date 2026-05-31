"use client";

import { useEffect, useRef } from "react";
import { TURNSTILE_SITE_KEY, isTurnstileEnabled, loadTurnstile } from "@/lib/turnstile";

/**
 * Widget Turnstile auto-rendu. N'affiche rien si la clé site n'est pas
 * configurée (mode FAKE local/dev). Émet le token via `onVerify`.
 */
export function TurnstileWidget({ onVerify }: { onVerify: (token: string) => void }) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isTurnstileEnabled() || !containerRef.current) return;
    let widgetId: string | null = null;
    loadTurnstile().then(() => {
      const ts = (window as unknown as { turnstile?: { render: (el: HTMLElement, opts: object) => string; remove: (id: string) => void } }).turnstile;
      if (!ts || !containerRef.current) return;
      widgetId = ts.render(containerRef.current, {
        sitekey: TURNSTILE_SITE_KEY,
        callback: (token: string) => onVerify(token),
        "error-callback": () => onVerify(""),
        "expired-callback": () => onVerify(""),
        theme: "dark",
      });
    });
    return () => {
      if (widgetId) {
        const ts = (window as unknown as { turnstile?: { remove: (id: string) => void } }).turnstile;
        ts?.remove(widgetId);
      }
    };
  }, [onVerify]);

  if (!isTurnstileEnabled()) return null;
  return <div ref={containerRef} className="mt-2" />;
}
