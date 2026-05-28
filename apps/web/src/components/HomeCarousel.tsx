"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useT } from "@/lib/i18n";

export type CarouselSlide = {
  kind: "live" | "category";
  href: string;
  title: string;
  subtitle: string;
  image: string;
  viewers?: number;
  accent: string;
};

const INTERVAL_MS = 6000;

export function HomeCarousel({ slides }: { slides: CarouselSlide[] }) {
  const t = useT();
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const touchX = useRef<number | null>(null);
  const count = slides.length;

  const go = useCallback(
    (next: number) => setIndex(((next % count) + count) % count),
    [count],
  );

  useEffect(() => {
    if (paused || count <= 1) return;
    const id = setInterval(() => setIndex((i) => (i + 1) % count), INTERVAL_MS);
    return () => clearInterval(id);
  }, [paused, count]);

  if (count === 0) return null;

  return (
    <section
      className="relative mb-10 overflow-hidden rounded-2xl border border-neutral-800"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onTouchStart={(e) => (touchX.current = e.touches[0].clientX)}
      onTouchEnd={(e) => {
        if (touchX.current === null) return;
        const dx = e.changedTouches[0].clientX - touchX.current;
        if (Math.abs(dx) > 40) go(index + (dx < 0 ? 1 : -1));
        touchX.current = null;
      }}
      aria-roledescription="carousel"
    >
      <div
        className="flex transition-transform duration-500 ease-out"
        style={{ transform: `translateX(-${index * 100}%)` }}
      >
        {slides.map((s, i) => (
          <Link
            key={`${s.kind}-${s.href}-${i}`}
            href={s.href}
            className="relative block h-64 w-full shrink-0 sm:h-80"
            aria-hidden={i !== index}
            tabIndex={i === index ? 0 : -1}
          >
            {s.image ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={s.image}
                alt=""
                className="absolute inset-0 h-full w-full object-cover"
              />
            ) : (
              <div
                className="absolute inset-0"
                style={{
                  background: `linear-gradient(135deg, ${s.accent}33, #0a0a0a 70%)`,
                }}
              />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />
            <div className="absolute bottom-0 left-0 max-w-2xl p-6 sm:p-8">
              <div className="mb-2 flex items-center gap-2">
                {s.kind === "live" ? (
                  <span className="rounded bg-red-500 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-neutral-950">
                    LIVE
                  </span>
                ) : (
                  <span
                    className="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-neutral-950"
                    style={{ backgroundColor: s.accent }}
                  >
                    {t("home.slide.category")}
                  </span>
                )}
                {typeof s.viewers === "number" && (
                  <span className="rounded bg-black/60 px-1.5 py-0.5 text-xs text-neutral-100">
                    {t("card.viewers", { n: s.viewers.toLocaleString("fr-FR") })}
                  </span>
                )}
              </div>
              <h2 className="line-clamp-2 text-2xl font-extrabold tracking-tight text-white sm:text-3xl">
                {s.title}
              </h2>
              <p className="mt-1 line-clamp-1 text-sm text-neutral-300">{s.subtitle}</p>
            </div>
          </Link>
        ))}
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
            {slides.map((_, i) => (
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
