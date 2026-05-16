import Link from "next/link";

export type LiveChannel = {
  slug: string;
  title: string;
  thumbnail_url: string;
  is_live: boolean;
  viewers?: number;
  streamer: { username: string; display_name: string; avatar_url: string };
  category: { slug: string; name: string } | null;
};

export function LiveCard({ channel }: { channel: LiveChannel }) {
  const display = channel.streamer.display_name || `@${channel.slug}`;
  return (
    <Link
      href={`/c/${channel.slug}`}
      className="group block overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900/60 transition hover:border-neutral-700"
    >
      <div className="relative aspect-video w-full bg-neutral-800">
        {channel.thumbnail_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={channel.thumbnail_url}
            alt={channel.title || display}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-neutral-600">
            Pas de vignette
          </div>
        )}
        {channel.is_live && (
          <span className="absolute left-2 top-2 rounded bg-red-500 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-neutral-950">
            LIVE
          </span>
        )}
        {typeof channel.viewers === "number" && (
          <span className="absolute bottom-2 left-2 rounded bg-black/70 px-2 py-0.5 text-xs text-neutral-100">
            {channel.viewers.toLocaleString("fr-FR")} viewers
          </span>
        )}
      </div>
      <div className="space-y-1 p-3">
        <p className="line-clamp-1 text-sm font-semibold">
          {channel.title || "Sans titre"}
        </p>
        <p className="text-xs text-neutral-400">
          {display} <span className="text-neutral-600">@{channel.slug}</span>
        </p>
        {channel.category && (
          <p className="text-xs text-neutral-500">{channel.category.name}</p>
        )}
      </div>
    </Link>
  );
}
