"use client";

// Fil « Instant » (Shorts) : vidéos courtes verticales les plus populaires de la
// plateforme, y compris de créateurs que l'utilisateur ne suit pas encore.
// Défilement vertical aimanté, lecture automatique sans son de la vidéo visible.

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FollowButton } from "@/components/FollowButton";
import { ShortVideo } from "@/components/ShortVideo";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

export type ShortItem = {
  id: number;
  title: string;
  thumbnail_url: string;
  playback_url: string;
  duration_s: number;
  view_count: number;
  like_count: number;
  published_at: string;
  liked: boolean;
  channel: {
    slug: string;
    is_live: boolean;
    streamer: { username: string; display_name: string; avatar_url: string };
  };
};

type Page = { results: ShortItem[]; next_offset: number | null };

const PAGE_SIZE = 10;

export default function InstantPage() {
  const t = useT();
  const { user, loading: authLoading, authFetch } = useAuth();
  const [items, setItems] = useState<ShortItem[]>([]);
  const [nextOffset, setNextOffset] = useState<number | null>(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [muted, setMuted] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const observer = useRef<IntersectionObserver | null>(null);

  const loadMore = useCallback(async () => {
    if (nextOffset === null || loadingMore) return;
    setLoadingMore(true);
    try {
      const fetcher = user ? authFetch : apiFetch;
      const page = await fetcher<Page>(
        `/api/shorts/trending?limit=${PAGE_SIZE}&offset=${nextOffset}`,
      );
      setItems((prev) => {
        const seen = new Set(prev.map((s) => s.id));
        return [...prev, ...page.results.filter((s) => !seen.has(s.id))];
      });
      setNextOffset(page.next_offset);
    } catch {
      setNextOffset(null);
    } finally {
      setLoadingMore(false);
      setLoaded(true);
    }
  }, [nextOffset, loadingMore, user, authFetch]);

  // Premier chargement une fois l'auth résolue (sinon « liked » serait faux
  // pour un utilisateur connecté). Lien partagé (?v=<id>) affiché en premier.
  const started = useRef(false);
  useEffect(() => {
    if (authLoading || started.current) return;
    started.current = true;
    const shared = Number(new URLSearchParams(window.location.search).get("v"));
    const start = async () => {
      if (shared) {
        try {
          const first = await (user ? authFetch : apiFetch)<ShortItem>(`/api/shorts/${shared}`);
          setItems([first]);
        } catch {
          /* vidéo indisponible : fil normal */
        }
      }
      loadMore();
    };
    start();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading]);

  // La vidéo la plus visible devient active ; charge la suite à l'avant-dernière.
  useEffect(() => {
    observer.current = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting && entry.intersectionRatio >= 0.6) {
            setActiveId(Number((entry.target as HTMLElement).dataset.id));
          }
        }
      },
      { threshold: [0.6] },
    );
    return () => observer.current?.disconnect();
  }, []);

  useEffect(() => {
    if (activeId === null || items.length === 0) return;
    const idx = items.findIndex((s) => s.id === activeId);
    if (idx >= items.length - 2) loadMore();
  }, [activeId, items, loadMore]);

  const register = useCallback((el: HTMLElement | null) => {
    if (el) observer.current?.observe(el);
  }, []);

  if (loaded && items.length === 0) {
    return (
      <main className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
        <h1 className="text-2xl font-bold">{t("shorts.title")}</h1>
        <p className="mt-2 max-w-sm text-sm text-neutral-400">{t("shorts.empty")}</p>
      </main>
    );
  }

  return (
    <main className="relative">
      <h1 className="sr-only">{t("shorts.title")}</h1>
      <button
        type="button"
        onClick={() => setMuted((m) => !m)}
        className="fixed right-4 top-20 z-30 rounded-full bg-black/60 px-3 py-1.5 text-xs font-semibold text-white backdrop-blur hover:bg-black/80"
      >
        {muted ? t("shorts.unmute") : t("shorts.mute")}
      </button>
      <div className="h-[calc(100vh-57px)] snap-y snap-mandatory overflow-y-auto">
        {items.map((s) => (
          <section
            key={s.id}
            ref={register}
            data-id={s.id}
            className="flex h-[calc(100vh-57px)] snap-start items-center justify-center py-3"
          >
            <ShortCard
              item={s}
              active={s.id === activeId}
              muted={muted}
              onChange={(next) =>
                setItems((prev) => prev.map((p) => (p.id === next.id ? next : p)))
              }
            />
          </section>
        ))}
        {loadingMore && (
          <p className="py-6 text-center text-sm text-neutral-500">{t("common.loading")}</p>
        )}
      </div>
    </main>
  );
}

function ShortCard({
  item,
  active,
  muted,
  onChange,
}: {
  item: ShortItem;
  active: boolean;
  muted: boolean;
  onChange: (next: ShortItem) => void;
}) {
  const t = useT();
  const { num } = useFormat();
  const router = useRouter();
  const { user, authFetch } = useAuth();
  const [shared, setShared] = useState(false);
  const name = item.channel.streamer.display_name || `@${item.channel.slug}`;

  const onWatched = useCallback(() => {
    apiFetch(`/api/shorts/${item.id}/view`, { method: "POST" }).catch(() => undefined);
  }, [item.id]);

  async function toggleLike() {
    if (!user) {
      router.push("/login");
      return;
    }
    const liked = !item.liked;
    onChange({ ...item, liked, like_count: item.like_count + (liked ? 1 : -1) });
    try {
      const res = await authFetch<{ like_count: number }>(`/api/shorts/${item.id}/like`, {
        method: liked ? "POST" : "DELETE",
      });
      onChange({ ...item, liked, like_count: res.like_count });
    } catch {
      onChange(item);
    }
  }

  async function share() {
    const url = `${window.location.origin}/instant?v=${item.id}`;
    try {
      if (navigator.share) await navigator.share({ title: item.title, url });
      else await navigator.clipboard.writeText(url);
      setShared(true);
      setTimeout(() => setShared(false), 2000);
    } catch {
      /* partage annulé */
    }
  }

  return (
    <article className="relative flex h-full max-h-[860px] items-end gap-3">
      <div className="relative aspect-[9/16] h-full overflow-hidden rounded-2xl bg-black shadow-2xl">
        <ShortVideo
          src={item.playback_url}
          poster={item.thumbnail_url}
          active={active}
          muted={muted}
          onWatched={onWatched}
        />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent p-4">
          <div className="pointer-events-auto flex items-center gap-2">
            <Link href={`/c/${item.channel.slug}`} className="flex min-w-0 items-center gap-2">
              {item.channel.streamer.avatar_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={item.channel.streamer.avatar_url}
                  alt=""
                  className="h-9 w-9 shrink-0 rounded-full object-cover ring-2 ring-white/20"
                />
              ) : (
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-neutral-700 text-sm text-white">
                  {name.replace(/^@/, "").charAt(0).toUpperCase()}
                </span>
              )}
              <span className="truncate text-sm font-semibold text-white">{name}</span>
              {item.channel.is_live && (
                <span className="rounded bg-secondary px-1.5 py-0.5 text-[10px] font-bold uppercase text-neutral-950">
                  {t("live.badge.on")}
                </span>
              )}
            </Link>
            <FollowButton username={item.channel.slug} />
          </div>
          <p className="mt-2 line-clamp-2 text-sm text-white">{item.title}</p>
          <p className="mt-1 text-xs text-neutral-300">
            {t("shorts.views", { n: num(item.view_count) })}
          </p>
        </div>
      </div>

      <div className="flex flex-col items-center gap-4 pb-6">
        <ActionButton
          label={t("shorts.like")}
          count={num(item.like_count)}
          active={item.liked}
          onClick={toggleLike}
        >
          <path d="M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.6l-1-1a5.5 5.5 0 00-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 000-7.8z" />
        </ActionButton>
        <ActionButton label={shared ? t("shorts.copied") : t("shorts.share")} onClick={share}>
          <path d="M4 12v8h16v-8M12 3v13M7 8l5-5 5 5" />
        </ActionButton>
      </div>
    </article>
  );
}

function ActionButton({
  label,
  count,
  active,
  onClick,
  children,
}: {
  label: string;
  count?: string;
  active?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      aria-label={label}
      className="flex flex-col items-center gap-1 text-xs text-neutral-300"
    >
      <span
        className={`flex h-11 w-11 items-center justify-center rounded-full transition active:scale-90 ${
          active ? "bg-secondary text-neutral-950" : "bg-neutral-800 hover:bg-neutral-700"
        }`}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill={active ? "currentColor" : "none"}
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
        >
          {children}
        </svg>
      </span>
      {count ?? label}
    </button>
  );
}
