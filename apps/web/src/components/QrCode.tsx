"use client";

import { useEffect, useState } from "react";

/** Rend une valeur (ex. URI otpauth) en QR code, généré côté client. */
export function QrCode({ value, size = 176 }: { value: string; size?: number }) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    import("qrcode")
      .then((QR) =>
        QR.toDataURL(value, {
          margin: 1,
          width: size,
          color: { dark: "#0a0a0a", light: "#ffffff" },
        }),
      )
      .then((url) => active && setSrc(url))
      .catch(() => active && setSrc(null));
    return () => {
      active = false;
    };
  }, [value, size]);

  if (!src) {
    return (
      <div
        style={{ width: size, height: size }}
        className="animate-pulse rounded-lg bg-neutral-800"
        aria-hidden
      />
    );
  }
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={src} alt="QR code" width={size} height={size} className="rounded-lg" />;
}
