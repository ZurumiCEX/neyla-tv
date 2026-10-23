"use client";

// Player HLS basé sur hls.js (flux Bunny Stream). Charge la lib dynamiquement
// (réduit le bundle initial) et utilise le support natif quand il existe (Safari).
// - `isLive === false` : carte « hors ligne » avec la vignette, pas de lecteur.
// - Erreur fatale : nouvelles tentatives automatiques (le flux peut mettre
//   quelques secondes à apparaître après le démarrage d'OBS).

import { useEffect, useRef, useState } from "react";
import { useT } from "@/lib/i18n";

type Props = {
  src: string;
  poster?: string;
  className?: string;
  isLive?: boolean;
  /** Lecture en boucle sans contrôles (Shorts). */
  loop?: boolean;
  controls?: boolean;
  autoPlay?: boolean;
  muted?: boolean;
};

const RETRY_DELAY_MS = 5_000;
const MAX_RETRIES = 12;

export function HlsPlayer({
  src,
  poster,
  className,
  isLive = true,
  loop = false,
  controls = true,
  autoPlay = true,
  muted = true,
}: Props) {
  const t = useT();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  const playable = Boolean(src) && isLive;

  useEffect(() => {
    setAttempt(0);
    setError(null);
  }, [src, isLive]);

  useEffect(() => {
    if (!playable) return;
    const video = videoRef.current;
    if (!video) return;

    let hls: import("hls.js").default | null = null;
    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    const scheduleRetry = () => {
      if (cancelled) return;
      if (attempt >= MAX_RETRIES) {
        setError(t("player.error"));
        return;
      }
      setError(t("player.retrying"));
      retryTimer = setTimeout(() => setAttempt((a) => a + 1), RETRY_DELAY_MS);
    };

    const isHls = src.includes(".m3u8");
    // MP4 direct ou support HLS natif (Safari).
    if (!isHls || video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
      const onError = () => scheduleRetry();
      const onPlaying = () => setError(null);
      video.addEventListener("error", onError);
      video.addEventListener("playing", onPlaying);
      return () => {
        cancelled = true;
        video.removeEventListener("error", onError);
        video.removeEventListener("playing", onPlaying);
        if (retryTimer) clearTimeout(retryTimer);
      };
    }

    (async () => {
      try {
        const { default: Hls } = await import("hls.js");
        if (cancelled) return;
        if (!Hls.isSupported()) {
          setError(t("player.unsupported"));
          return;
        }
        hls = new Hls({ enableWorker: true, lowLatencyMode: true });
        hls.loadSource(src);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, () => setError(null));
        hls.on(Hls.Events.ERROR, (_event, data) => {
          if (!data.fatal) return;
          hls?.destroy();
          hls = null;
          scheduleRetry();
        });
      } catch {
        setError(t("player.loadFail"));
      }
    })();

    return () => {
      cancelled = true;
      if (retryTimer) clearTimeout(retryTimer);
      if (hls) hls.destroy();
    };
  }, [src, playable, attempt, t]);

  if (!playable) {
    return (
      <div
        className={`relative flex aspect-video w-full items-center justify-center overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 text-center ${className ?? ""}`}
      >
        {poster && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={poster} alt="" className="absolute inset-0 h-full w-full object-cover opacity-25" />
        )}
        <div className="relative px-6">
          <p className="text-lg font-semibold text-neutral-100">{t("player.offline")}</p>
          <p className="mt-2 text-sm text-neutral-400">{t("player.offlineHint")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`overflow-hidden rounded-xl bg-black ${className ?? ""}`}>
      <video
        ref={videoRef}
        controls={controls}
        autoPlay={autoPlay}
        muted={muted}
        loop={loop}
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
