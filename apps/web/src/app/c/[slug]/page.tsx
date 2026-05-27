import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";
import { ChatPanel } from "@/components/ChatPanel";
import { FollowButton } from "@/components/FollowButton";
import { HlsPlayer } from "@/components/HlsPlayer";
import { LiveBadge } from "@/components/LiveBadge";
import { SocialLinks } from "@/components/SocialLinks";
import { apiFetchServer } from "@/lib/api";

type PublicChannel = {
  slug: string;
  title: string;
  thumbnail_url: string;
  banner_url: string;
  social_links: Record<string, string>;
  hls_playback_url: string;
  is_live: boolean;
  last_live_started_at: string | null;
  streamer: { username: string; display_name: string; avatar_url: string; bio: string };
  category: { slug: string; name: string } | null;
};

async function getChannel(slug: string): Promise<PublicChannel | null> {
  try {
    return await apiFetchServer<PublicChannel>(`/api/channels/${slug}`);
  } catch (err) {
    const e = err as { status?: number };
    if (e.status === 404) return null;
    throw err;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const channel = await getChannel(slug);
  if (!channel) return { title: "Chaîne introuvable" };
  return {
    title: `${channel.streamer.display_name || `@${channel.slug}`} — Neyla TV`,
    description: channel.title || `La chaîne de @${channel.slug}`,
  };
}

export default async function ChannelPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const channel = await getChannel(slug);
  if (!channel) notFound();

  const displayName = channel.streamer.display_name || `@${channel.slug}`;

  return (
    <main className="mx-auto max-w-6xl px-4 py-6">
      {channel.banner_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={channel.banner_url}
          alt=""
          className="mb-4 h-40 w-full rounded-xl object-cover"
        />
      )}
      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        <div>
          <HlsPlayer src={channel.hls_playback_url} poster={channel.thumbnail_url} />
          <header className="mt-4 flex items-start justify-between gap-4">
            <div>
              <h1 className="text-xl font-bold">{channel.title || "Aucun titre"}</h1>
              <p className="mt-1 text-sm text-neutral-400">
                par <span className="text-neutral-200">{displayName}</span>{" "}
                <span className="text-neutral-500">@{channel.slug}</span>
              </p>
              {channel.category && (
                <Link
                  href={`/categories/${channel.category.slug}`}
                  className="mt-2 inline-block rounded-full border border-neutral-700 px-3 py-0.5 text-xs text-neutral-300 hover:border-emerald-500"
                >
                  {channel.category.name}
                </Link>
              )}
            </div>
            <div className="flex items-center gap-3">
              <LiveBadge slug={channel.slug} initial={{ is_live: channel.is_live }} />
              <FollowButton username={channel.slug} />
            </div>
          </header>

          {channel.streamer.bio && (
            <p className="mt-4 whitespace-pre-line text-sm text-neutral-300">
              {channel.streamer.bio}
            </p>
          )}
          <SocialLinks links={channel.social_links} />
        </div>

        <aside>
          <ChatPanel slug={channel.slug} isLive={channel.is_live} />
        </aside>
      </div>
    </main>
  );
}
