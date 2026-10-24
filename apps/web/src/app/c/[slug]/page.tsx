import { notFound } from "next/navigation";
import type { Metadata } from "next";
import type { AchievementItem } from "@/components/AchievementIcon";
import { LiveStage } from "@/components/LiveStage";
import { ChannelAbout } from "@/components/channel/ChannelAbout";
import { ChannelGoalCard, type ChannelGoal } from "@/components/channel/ChannelGoalCard";
import { ChannelHeader } from "@/components/channel/ChannelHeader";
import { ChannelLayout } from "@/components/channel/ChannelLayout";
import { ChannelShorts } from "@/components/channel/ChannelShorts";
import { apiFetchServer } from "@/lib/api";
import { getServerT } from "@/lib/i18n-server";

type PublicChannel = {
  slug: string;
  title: string;
  thumbnail_url: string;
  banner_url: string;
  social_links: Record<string, string>;
  playback_url: string;
  is_live: boolean;
  last_live_started_at: string | null;
  streamer: { username: string; display_name: string; avatar_url: string; bio: string };
  category: { slug: string; name: string } | null;
  tags: string[];
  follower_count: number;
  is_verified: boolean;
  show_viewer_count?: boolean;
  goal: ChannelGoal | null;
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
  const [t, channel] = await Promise.all([getServerT(), getChannel(slug)]);
  if (!channel) return { title: t("channel.notFound") };
  return {
    title: `${channel.streamer.display_name || `@${channel.slug}`} — Neyla TV`,
    description: channel.title || `La chaîne de @${channel.slug}`,
  };
}

export default async function ChannelPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const channel = await getChannel(slug);
  if (!channel) notFound();

  const displayName = channel.streamer.display_name || `@${channel.slug}`;
  const followers = channel.follower_count ?? 0;

  // Succès débloqués du streamer (public) : badges profil + pastille avatar.
  const achievements = await apiFetchServer<{ results: AchievementItem[]; unlocked: number }>(
    `/api/achievements/${channel.streamer.username}`,
  ).catch(() => ({ results: [], unlocked: 0 }));

  return (
    <main className="w-full">
      <ChannelLayout
        slug={channel.slug}
        isLive={channel.is_live}
        stage={
          <LiveStage
            slug={channel.slug}
            src={channel.playback_url}
            poster={channel.thumbnail_url || channel.banner_url}
            initialLive={channel.is_live}
            className="!rounded-none !border-0"
          />
        }
      >
        <ChannelHeader
          slug={channel.slug}
          username={channel.streamer.username}
          displayName={displayName}
          avatarUrl={channel.streamer.avatar_url}
          title={channel.title}
          isLive={channel.is_live}
          isVerified={Boolean(channel.is_verified)}
          liveStartedAt={channel.last_live_started_at}
          category={channel.category}
          tags={channel.tags ?? []}
          achievements={achievements.unlocked}
          showViewers={channel.show_viewer_count !== false}
        />
        <div className="grid gap-4 p-4 sm:p-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,420px)]">
          <ChannelAbout
            name={displayName}
            username={channel.streamer.username}
            followers={followers}
            bio={channel.streamer.bio}
            socialLinks={channel.social_links}
            achievements={achievements.results}
          />
          <ChannelGoalCard goal={channel.goal} followers={followers} />
        </div>
        <div className="px-4 pb-6 sm:px-6">
          <ChannelShorts slug={channel.slug} />
        </div>
      </ChannelLayout>
    </main>
  );
}
