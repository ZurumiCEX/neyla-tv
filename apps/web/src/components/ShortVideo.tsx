"use client";

// Lecteur d'une vidéo « Instant » : MP4 direct ou HLS Bunny (hls.js chargé à la
// demande). Lecture uniquement quand `active` (vidéo visible dans le fil).

import { useEffect, useRef } from "react";

type Props = {
  src: string;
  poster?: string;
  active: boolean;
  muted: boolean;
  onWatched?: () => void;
};

const WATCHED_AFTER_MS = 2_000;

export function ShortVideo({ src, poster, active, muted, onWatched }: Props) {
  const ref = useRef<HTMLVideoElement | null>(null);
  const watchedRef = useRef(false);

  // Attache la source (HLS via hls.js si nécessaire).
  useEffect(() => {
    const video = ref.current;
    if (!video || !src) return;
    let hls: import("hls.js").default | null = null;
    let cancelled = false;
    const isHls = src.includes(".m3u8");
    if (!isHls || video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
    } else {
      (async () => {
        const { default: Hls } = await import("hls.js");
        if (cancelled || !Hls.isSupported()) return;
        hls = new Hls({ enableWorker: true });
        hls.loadSource(src);
        hls.attachMedia(video);
      })();
    }
    return () => {
      cancelled = true;
      if (hls) hls.destroy();
    };
  }, [src]);

  // Lecture / pause selon la visibilité ; « vue » comptée après 2 s.
  useEffect(() => {
    const video = ref.current;
    if (!video) return;
    if (!active) {
      video.pause();
      return;
    }
    video.currentTime = 0;
    video.play().catch(() => undefined);
    const timer = setTimeout(() => {
      if (!watchedRef.current) {
        watchedRef.current = true;
        onWatched?.();
      }
    }, WATCHED_AFTER_MS);
    return () => clearTimeout(timer);
  }, [active, onWatched]);

  useEffect(() => {
    if (ref.current) ref.current.muted = muted;
  }, [muted]);

  return (
    <video
      ref={ref}
      poster={poster}
      muted={muted}
      loop
      playsInline
      preload={active ? "auto" : "metadata"}
      onClick={(e) => {
        const v = e.currentTarget;
        if (v.paused) v.play().catch(() => undefined);
        else v.pause();
      }}
      className="h-full w-full cursor-pointer bg-black object-cover"
    />
  );
}
