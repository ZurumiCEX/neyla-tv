"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Eye, Zap } from "lucide-react";
import { EmojiText } from "@/components/Emoji";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

type Short = {
  id: number;
  title: string;
  thumbnail_url: string;
  duration_s: number;
  view_count: number;
};

/** Vidéos Instant de la chaîne (GET /api/channels/<slug>/shorts). */
export function ChannelShorts({ slug }: { slug: string }) {
  const t = useT();
  const { num } = useFormat();
  const [items, setItems] = useState<Short[] | null>(null);

  useEffect(() => {
    apiFetch<{ results: Short[] }>(`/api/channels/${slug}/shorts?limit=12`)
      .then((d) => setItems(d.results))
      .catch(() => setItems([]));
  }, [slug]);

  if (!items || items.length === 0) return null;
  return (
    <section className="rounded-xl bg-neutral-900 p-4 sm:p-5">
      <h2 className="mb-3 flex items-center gap-2 text-lg font-bold">
        <Zap size={18} className="text-emerald-400" aria-hidden />
        {t("channel.shorts")}
      </h2>
      <ul className="grid grid-cols-3 gap-2 sm:grid-cols-4 lg:grid-cols-6">
        {items.map((s) => (
          <li key={s.id}>
            <Link href={`/instant?v=${s.id}`} className="group block">
              <div className="relative aspect-[9/16] overflow-hidden rounded-lg bg-neutral-800">
                {s.thumbnail_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={s.thumbnail_url}
                    alt=""
                    loading="lazy"
                    onError={(e) => (e.currentTarget.style.visibility = "hidden")}
                    className="h-full w-full object-cover transition group-hover:scale-105"
                  />
                )}
                <span className="absolute bottom-1 left-1 flex items-center gap-1 rounded bg-black/70 px-1.5 text-[11px] font-semibold text-white">
                  <Eye size={11} aria-hidden /> {num(s.view_count)}
                </span>
                <span className="absolute bottom-1 right-1 rounded bg-black/70 px-1.5 text-[11px] text-white">
                  0:{String(s.duration_s).padStart(2, "0")}
                </span>
              </div>
              <p className="mt-1 line-clamp-2 text-xs font-semibold text-neutral-200 group-hover:text-emerald-300">
                <EmojiText text={s.title} size={13} />
              </p>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
