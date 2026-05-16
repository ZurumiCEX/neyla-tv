"use client";

// Player HLS basé sur hls.js. Charge la lib dynamiquement (réduit le bundle initial).
// Détecte le support natif (Safari iOS / macOS) et utilise video.src direct.
// En mode FAKE (URL contenant "fake.local"), affiche un placeholder.

import { useEffect, useRef, useState } from "react";

type Props = {
  src: string;
  poster?: string;
  className?: string;
};

const FAKE_HOST = "fake.local";

export function HlsPlayer({ src, poster, className }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isFake = src.includes(FAKE_HOST);

  useEffect(() => {
    if (!src || isFake) return;
    const video = videoRef.current;
    if (!video) return;

    // Support natif (Safari).
    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
      return;
    }

    let hls: import("hls.js").default | null = null;
    let cancelled = false;
    (async () => {
      try {
        const { default: Hls } = await import("hls.js");
        if (cancelled) return;
        if (!Hls.isSupported()) {
          setError("Lecture HLS non supportée par ce navigateur.");
          return;
        }
        hls = new Hls({ enableWorker: true, lowLatencyMode: true });
        hls.loadSource(src);
        hls.attachMedia(video);
        hls.on(Hls.Events.ERROR, (_event, data) => {
          if (data.fatal) setError("Erreur de lecture du flux.");
        });
      } catch {
        setError("Impossible de charger le lecteur.");
      }
    })();

    return () => {
      cancelled = true;
      if (hls) hls.destroy();
    };
  }, [src, isFake]);

  if (isFake) {
    return (
      <div
        className={`relative flex aspect-video w-full items-center justify-center overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 text-center ${className ?? ""}`}
      >
        <div className="px-6">
          <p className="text-lg font-semibold text-neutral-200">Mode démo</p>
          <p className="mt-2 text-sm text-neutral-400">
            Cloudflare Stream n&apos;est pas configuré : URL fictive.
            <br />
            Configure <code className="text-emerald-300">CLOUDFLARE_API_TOKEN</code> pour activer
            la lecture réelle.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`overflow-hidden rounded-xl bg-black ${className ?? ""}`}>
      <video
        ref={videoRef}
        controls
        autoPlay
        muted
        playsInline
        poster={poster}
        className="aspect-video w-full"
      />
      {error && (
        <p className="border-t border-red-500/40 bg-red-500/10 p-2 text-center text-sm text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
