"use client";

import { useEffect, useState } from "react";

// Fonds des initiales : stables par nom, lisibles avec un texte sombre.
const BG = ["#FFC81E", "#7dd3fc", "#f9a8d4", "#86efac", "#c4b5fd", "#fdba74", "#5eead4", "#fca5a5"];

function bgFor(name: string): string {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) | 0;
  return BG[Math.abs(h) % BG.length];
}

/**
 * Photo de profil avec repli sur l'initiale : URL vide, image cassée
 * (ancien lien fake.local, service externe hors ligne…) ou en cours de chargement.
 */
export function Avatar({
  src,
  name,
  size = 32,
  className = "",
  rounded = "full",
}: {
  src?: string | null;
  name: string;
  size?: number;
  className?: string;
  rounded?: "full" | "lg";
}) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);

  const radius = rounded === "full" ? "rounded-full" : "rounded-lg";
  const style = { width: size, height: size };
  if (src && !failed) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={src}
        alt=""
        width={size}
        height={size}
        loading="lazy"
        onError={() => setFailed(true)}
        className={`shrink-0 object-cover ${radius} ${className}`}
        style={style}
      />
    );
  }
  const initial = (name || "?").replace(/^@/, "").charAt(0).toUpperCase() || "?";
  return (
    <span
      aria-hidden
      className={`flex shrink-0 select-none items-center justify-center font-bold text-neutral-950 ${radius} ${className}`}
      style={{ ...style, background: bgFor(name || "?"), fontSize: Math.max(10, size * 0.42) }}
    >
      {initial}
    </span>
  );
}
