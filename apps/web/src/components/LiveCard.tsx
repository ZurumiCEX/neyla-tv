"use client";

import Link from "next/link";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";
import { Avatar } from "@/components/Avatar";
import { EmojiText } from "@/components/Emoji";

export type LiveChannel = {
  slug: string;
  title: string;
  thumbnail_url: string;
  is_live: boolean;
  viewers?: number;
  playback_url?: string;
  streamer: { username: string; display_name: string; avatar_url: string };
  category: { slug: string; name: string; group?: string } | null;
};

export function LiveCard({ channel }: { channel: LiveChannel }) {
  const t = useT();
  const { num } = useFormat();
  const display = channel.streamer.display_name || `@${channel.slug}`;

  return (
    <div className="group">
      <Link
        href={`/c/${channel.slug}`}
        className="relative block aspect-video w-full overflow-hidden rounded-lg bg-neutral-800 ring-emerald-500/0 transition group-hover:ring-2 group-hover:ring-emerald-500/60"
      >
        {channel.thumbnail_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={channel.thumbnail_url}
            alt={channel.title || display}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-neutral-600">
            {t("card.noThumb")}
          </div>
        )}
        {channel.is_live && (
          <span className="absolute left-2 top-2 flex items-center gap-1 rounded bg-secondary px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white" />
            LIVE
          </span>
        )}
        {typeof channel.viewers === "number" && (
          <span className="absolute bottom-2 left-2 flex items-center gap-1 rounded bg-black/70 px-1.5 py-0.5 text-xs text-neutral-100">
            <span className="h-2 w-2 rounded-[1px] bg-secondary" />
            {t("card.viewers", { n: num(channel.viewers) })}
          </span>
        )}
      </Link>

      <div className="mt-2 flex gap-2">
        <Link href={`/c/${channel.slug}`} className="shrink-0">
          <Avatar
            src={channel.streamer.avatar_url}
            name={channel.streamer.display_name || channel.slug}
            size={36}
          />
        </Link>
        <div className="min-w-0 flex-1">
          <Link
            href={`/c/${channel.slug}`}
            className="line-clamp-1 text-sm font-semibold text-neutral-100 hover:text-emerald-300"
            title={channel.title || t("card.untitled")}
          >
            <EmojiText text={channel.title || t("card.untitled")} size={16} />
          </Link>
          <p className="truncate text-xs text-neutral-400">{display}</p>
          {channel.category && (
            <Link
              href={`/categories/${channel.category.slug}`}
              className="truncate text-xs text-neutral-500 hover:text-emerald-300"
            >
              {channel.category.name}
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
