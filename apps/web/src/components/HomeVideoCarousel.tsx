"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useT } from "@/lib/i18n";

export type HeroVideo = { id: string; start?: number };

const ROTATE_MS = 5 * 60 * 1000; // 5 min → diapositive suivante
const VOLUME = 20; // niveau sonore bas (~20 %)

/** Charge l'IFrame Player API de YouTube une seule fois. */
let ytApiPromise: Promise<void> | null = null;
function loadYouTubeApi(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  const w = window as unknown as { YT?: { Player?: unknown }; onYouTubeIframeAPIReady?: () => void };
  if (w.YT && w.YT.Player) return Promise.resolve();
  if (ytApiPromise) return ytApiPromise;
  ytApiPromise = new Promise<void>((resolve) => {
    const previous = w.onYouTubeIframeAPIReady;
    w.onYouTubeIframeAPIReady = () => {
      previous?.();
      resolve();
    };
    const tag = document.createElement("script");
    tag.src = "https://www.youtube.com/iframe_api";
    document.head.appendChild(tag);
  });
  return ytApiPromise;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
export function HomeVideoCarousel({ videos }: { videos: HeroVideo[] }) {
  const t = useT();
  const count = videos.length;
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [muted, setMuted] = useState(true);

  const stageRef = useRef<HTMLDivElement | null>(null);
  const holderRef = useRef<HTMLDivElement | null>(null);
  const targetRef = useRef<HTMLDivElement | null>(null);
  const playerRef = useRef<any>(null);
  const indexRef = useRef(0);
  indexRef.current = index;

  const go = useCallback(
    (next: number) => setIndex(((next % count) + count) % count),
    [count],
  );

  const applySound = useCallback((player: any) => {
    try {
      player.setVolume(VOLUME);
      player.unMute(); // best-effort : certains navigateurs gardent le mute jusqu'à interaction
      setMuted(player.isMuted?.() ?? false);
    } catch {
      /* lecteur pas prêt */
    }
  }, []);

  // --- Initialise le lecteur une seule fois ---
  useEffect(() => {
    let cancelled = false;
    loadYouTubeApi().then(() => {
      if (cancelled || !targetRef.current) return;
      const YT = (window as any).YT;
      playerRef.current = new YT.Player(targetRef.current, {
        width: "100%",
        height: "100%",
        videoId: videos[0]?.id,
        host: "https://www.youtube-nocookie.com",
        playerVars: {
          autoplay: 1,
          mute: 1, // requis pour l'autoplay
          controls: 0,
          rel: 0,
          modestbranding: 1,
          playsinline: 1,
          fs: 0,
          disablekb: 1,
          iv_load_policy: 3,
          start: videos[0]?.start ?? 0,
        },
        events: {
          onReady: (e: any) => {
            applySound(e.target);
            try {
              e.target.playVideo();
            } catch {
              /* ignore */
            }
          },
          onStateChange: (e: any) => {
            if (e.data === YT.PlayerState.ENDED) go(indexRef.current + 1);
          },
        },
      });
    });
    return () => {
      cancelled = true;
      try {
        playerRef.current?.destroy();
      } catch {
        /* ignore */
      }
      playerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- Change de vidéo quand l'index bouge ---
  useEffect(() => {
    const p = playerRef.current;
    const v = videos[index];
    if (!p || typeof p.loadVideoById !== "function" || !v) return;
    p.loadVideoById({ videoId: v.id, startSeconds: v.start ?? 0 });
    applySound(p);
  }, [index, videos, applySound]);

  // --- Cadre « cover » : agrandit le holder 16:9 pour remplir la bannière ---
  useEffect(() => {
    const stage = stageRef.current;
    const holder = holderRef.current;
    if (!stage || !holder) return;
    const resize = () => {
      const w = stage.clientWidth;
      const h = stage.clientHeight;
      const scale = Math.max(w / 16, h / 9);
      holder.style.width = `${Math.ceil(16 * scale)}px`;
      holder.style.height = `${Math.ceil(9 * scale)}px`;
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(stage);
    return () => ro.disconnect();
  }, []);

  // --- Rotation automatique toutes les 5 min (en pause au survol) ---
  useEffect(() => {
    if (paused || count <= 1) return;
    const id = setTimeout(() => setIndex((i) => (i + 1) % count), ROTATE_MS);
    return () => clearTimeout(id);
  }, [paused, count, index]);

  function toggleSound() {
    const p = playerRef.current;
    if (!p) return;
    try {
      if (p.isMuted()) {
        p.unMute();
        p.setVolume(VOLUME);
        setMuted(false);
      } else {
        p.mute();
        setMuted(true);
      }
    } catch {
      /* ignore */
    }
  }

  if (count === 0) return null;

  return (
    <section
      className="relative mb-10 overflow-hidden rounded-2xl border border-neutral-800 bg-black"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      aria-roledescription="carousel"
    >
      <div ref={stageRef} className="relative h-64 w-full sm:h-80 md:h-96">
        {/* Vidéo en fond, recadrée pour remplir sans bandes noires */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div
            ref={holderRef}
            className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
          >
            <div ref={targetRef} className="h-full w-full" />
          </div>
        </div>

        {/* Dégradé + texte d'accroche */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />
        <div className="absolute bottom-0 left-0 max-w-2xl p-6 sm:p-8">
          <h2 className="text-2xl font-extrabold tracking-tight text-white sm:text-4xl">
            {t("home.heroTitle")}
          </h2>
          <p className="mt-2 max-w-xl text-sm text-neutral-300 sm:text-base">
            {t("home.heroSubtitle")}
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              href="/parcourir"
              className="rounded-lg bg-emerald-500 px-5 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
            >
              {t("home.heroBrowse")}
            </Link>
            <Link
              href="/become-streamer"
              className="rounded-lg border border-secondary bg-secondary/10 px-5 py-2 text-sm font-semibold text-secondary-light hover:bg-secondary/20"
            >
              {t("home.heroBecome")}
            </Link>
          </div>
        </div>

        {/* Bouton son */}
        <button
          type="button"
          onClick={toggleSound}
          aria-label={muted ? t("home.video.unmute") : t("home.video.mute")}
          className="absolute right-3 top-3 rounded-full bg-black/55 p-2 text-white hover:bg-black/75"
        >
          <SoundIcon muted={muted} />
        </button>
      </div>

      {count > 1 && (
        <>
          <button
            type="button"
            onClick={() => go(index - 1)}
            aria-label={t("home.slide.prev")}
            className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-black/50 p-2 text-white hover:bg-black/70"
          >
            <ChevronIcon dir="left" />
          </button>
          <button
            type="button"
            onClick={() => go(index + 1)}
            aria-label={t("home.slide.next")}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-black/50 p-2 text-white hover:bg-black/70"
          >
            <ChevronIcon dir="right" />
          </button>
          <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-1.5">
            {videos.map((_, i) => (
              <button
                key={i}
                type="button"
                onClick={() => go(i)}
                aria-label={t("home.slide.goTo", { n: i + 1 })}
                className={`h-1.5 rounded-full transition-all ${
                  i === index ? "w-6 bg-white" : "w-1.5 bg-white/40 hover:bg-white/70"
                }`}
              />
            ))}
          </div>
        </>
      )}
    </section>
  );
}
/* eslint-enable @typescript-eslint/no-explicit-any */

function SoundIcon({ muted }: { muted: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M4 9v6h4l5 4V5L8 9H4z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      {muted ? (
        <path d="M17 9l4 6M21 9l-4 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      ) : (
        <path
          d="M16 9a4 4 0 010 6"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      )}
    </svg>
  );
}

function ChevronIcon({ dir }: { dir: "left" | "right" }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d={dir === "left" ? "M15 18l-6-6 6-6" : "M9 6l6 6-6 6"}
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
