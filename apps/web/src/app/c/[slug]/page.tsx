import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { HlsPlayer } from "@/components/HlsPlayer";
import { LiveBadge } from "@/components/LiveBadge";
import { apiFetchServer } from "@/lib/api";

type PublicChannel = {
  slug: string;
  title: string;
  thumbnail_url: string;
  hls_playback_url: string;
  is_live: boolean;
  last_live_started_at: string | null;
  streamer: { username: string; display_name: string; avatar_url: string };
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
    <main className="mx-auto max-w-5xl px-4 py-6">
      <HlsPlayer src={channel.hls_playback_url} poster={channel.thumbnail_url} />

      <header className="mt-4 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold">{channel.title || "Aucun titre"}</h1>
          <p className="mt-1 text-sm text-neutral-400">
            par <span className="text-neutral-200">{displayName}</span>{" "}
            <span className="text-neutral-500">@{channel.slug}</span>
          </p>
        </div>
        <LiveBadge slug={channel.slug} initial={{ is_live: channel.is_live }} />
      </header>

      <section className="mt-8 rounded-xl border border-dashed border-neutral-800 p-6 text-center text-sm text-neutral-500">
        Chat live — disponible en Phase 4.
      </section>
    </main>
  );
}
