"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FollowButton } from "@/components/FollowButton";
import { AvatarBadge } from "@/components/ProfileAchievements";
import { ReportButton } from "@/components/ReportButton";
import { ShareButton } from "@/components/ShareButton";
import { SubscribeButton } from "@/components/SubscribeButton";
import { TipButton } from "@/components/TipButton";
import { GiftSubButton } from "@/components/channel/GiftSubButton";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";
import { useLiveStatus } from "@/lib/use-live-status";
import { Avatar } from "@/components/Avatar";

type Props = {
  slug: string;
  username: string;
  displayName: string;
  avatarUrl: string;
  title: string;
  isLive: boolean;
  isVerified: boolean;
  liveStartedAt: string | null;
  category: { slug: string; name: string } | null;
  tags: string[];
  achievements: number;
};

/** Bandeau sous le lecteur : identité, titre, catégorie, actions et audience. */
export function ChannelHeader(props: Props) {
  const t = useT();
  const { num } = useFormat();
  const { isLive, viewers } = useLiveStatus(props.slug, props.isLive);

  return (
    <section className="border-b border-neutral-800 px-4 py-4 sm:px-6">
      <div className="flex flex-wrap items-start gap-4">
        <AvatarBadge count={props.achievements}>
          <span
            className={`relative inline-flex rounded-full p-[3px] ${
              isLive ? "bg-emerald-500" : "bg-neutral-700"
            }`}
          >
            <Avatar
              src={props.avatarUrl}
              name={props.displayName}
              size={64}
              className="border-2 border-neutral-950"
            />
            {isLive && (
              <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 rounded bg-red-600 px-1.5 text-[10px] font-black uppercase leading-4 tracking-wider text-white">
                {t("live.badge.on")}
              </span>
            )}
          </span>
        </AvatarBadge>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <h1 className="truncate text-xl font-bold">{props.displayName}</h1>
            {props.isVerified && (
              <span title={t("channel.verified")} aria-label={t("channel.verified")}>
                <VerifiedIcon />
              </span>
            )}
          </div>
          <p className="mt-0.5 line-clamp-2 text-[15px] font-semibold text-neutral-100">
            {props.title || t("card.untitled")}
          </p>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            {props.category && (
              <Link
                href={`/categories/${props.category.slug}`}
                className="mr-1 text-sm font-semibold text-emerald-400 hover:underline"
              >
                {props.category.name}
              </Link>
            )}
            {props.tags.map((tag) => (
              <Link
                key={tag}
                href={`/search?q=${encodeURIComponent(tag)}`}
                className="rounded-full bg-neutral-800 px-2.5 py-0.5 text-xs font-medium text-neutral-300 hover:bg-neutral-700"
              >
                {tag}
              </Link>
            ))}
          </div>
        </div>

        <div className="flex w-full flex-col items-stretch gap-2 sm:w-auto sm:items-end">
          <div className="flex flex-wrap items-center gap-2 sm:justify-end">
            <FollowButton username={props.slug} />
            <GiftSubButton channelSlug={props.slug} />
            <SubscribeButton channelSlug={props.slug} />
            <TipButton channelSlug={props.slug} />
          </div>
          <div className="flex items-center gap-3 text-sm sm:justify-end">
            {isLive && viewers !== null && (
              <span className="flex items-center gap-1.5 font-semibold text-neutral-100">
                <UserIcon />
                <span className="tabular-nums">{num(viewers)}</span>
              </span>
            )}
            {isLive && props.liveStartedAt && <Uptime since={props.liveStartedAt} />}
            <ShareButton
              compact
              path={`/c/${props.slug}`}
              title={`${props.title} — @${props.username}`}
            />
            <ReportButton compact channelSlug={props.slug} targetUsername={props.username} />
          </div>
        </div>
      </div>
    </section>
  );
}

/** Durée du live en cours (hh:mm:ss), mise à jour chaque seconde. */
function Uptime({ since }: { since: string }) {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now());
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  if (now === null) return null;
  const secs = Math.max(0, Math.floor((now - new Date(since).getTime()) / 1000));
  const pad = (n: number) => String(n).padStart(2, "0");
  const label = `${pad(Math.floor(secs / 3600))}:${pad(Math.floor((secs % 3600) / 60))}:${pad(secs % 60)}`;
  return <span className="tabular-nums text-neutral-400">{label}</span>;
}

function VerifiedIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden className="text-emerald-400">
      <path
        fill="currentColor"
        d="M12 1l2.6 2.2 3.4-.4.9 3.3 3 1.7-1.2 3.2 1.2 3.2-3 1.7-.9 3.3-3.4-.4L12 23l-2.6-2.2-3.4.4-.9-3.3-3-1.7L3.3 13 2.1 9.8l3-1.7.9-3.3 3.4.4z"
      />
      <path
        d="M8 12.5l2.7 2.7L16.5 9"
        fill="none"
        stroke="#0a0a0a"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 12a5 5 0 100-10 5 5 0 000 10zm0 2c-4.4 0-8 2.2-8 5v3h16v-3c0-2.8-3.6-5-8-5z" />
    </svg>
  );
}
