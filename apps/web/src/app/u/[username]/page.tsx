"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { AchievementIcon, type AchievementItem } from "@/components/AchievementIcon";
import { Avatar } from "@/components/Avatar";
import { GiftBadge, giftTierByKey } from "@/components/GiftBadge";
import { LevelBadge, levelByKey, type LevelProgress } from "@/components/LevelBadge";
import { achText } from "@/lib/achievements";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

type Supported = {
  slug: string;
  display_name: string;
  avatar_url: string;
  gift_tier: string | null;
  total_aura?: number;
};

type Profile = {
  username: string;
  display_name: string;
  avatar_url: string;
  bio: string;
  joined_at: string;
  is_owner: boolean;
  channel: { slug: string; is_live: boolean } | null;
  level: LevelProgress;
  supported: Supported[];
  achievements: AchievementItem[];
  achievements_unlocked: number;
  following_count: number;
  follower_count: number;
};

export default function ProfilePage({ params }: { params: Promise<{ username: string }> }) {
  const { username } = use(params);
  const t = useT();
  const { num, date } = useFormat();
  const { user, loading, authFetch } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    if (loading) return;
    const path = `/api/users/${encodeURIComponent(username)}/profile`;
    // Connecté : la requête authentifiée révèle les montants si c'est son propre profil.
    const load = user ? authFetch<Profile>(path) : apiFetch<Profile>(path);
    load.then(setProfile).catch(() => setMissing(true));
  }, [username, user, loading, authFetch]);

  if (missing) {
    return (
      <main className="mx-auto max-w-3xl p-8 text-center">
        <h1 className="text-xl font-bold">{t("profile.notFound")}</h1>
        <Link href="/" className="mt-3 inline-block text-sm text-emerald-300 hover:underline">
          {t("profile.backHome")}
        </Link>
      </main>
    );
  }
  if (!profile) return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;

  const level = levelByKey(profile.level.level);
  const next = levelByKey(profile.level.next_level);
  const accent = level?.color ?? "#71717a";
  const remaining =
    profile.level.next_at !== null && typeof profile.level.spent === "number"
      ? profile.level.next_at - profile.level.spent
      : null;

  return (
    <main className="mx-auto w-full max-w-5xl space-y-5 p-4 sm:p-6">
      {/* En-tête */}
      <section className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/60">
        <div
          className="h-28 sm:h-36"
          style={{ background: `linear-gradient(120deg, ${accent}55, #0a0a0a 70%)` }}
        />
        <div className="-mt-12 flex flex-wrap items-end gap-4 px-4 pb-5 sm:px-6">
          <span className="relative">
            <Avatar
              src={profile.avatar_url}
              name={profile.display_name}
              size={96}
              className="border-4 border-neutral-950"
            />
            <span className="absolute -bottom-1 -right-1">
              <LevelBadge level={profile.level.level} size={36} />
            </span>
          </span>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-2xl font-bold">{profile.display_name}</h1>
            <p className="text-sm text-neutral-400">
              @{profile.username} · {t("profile.joined", { date: date(profile.joined_at, { month: "long", year: "numeric" }) })}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {profile.channel && (
              <Link
                href={`/c/${profile.channel.slug}`}
                className="flex h-9 items-center gap-2 rounded-md bg-emerald-500 px-4 text-sm font-bold text-neutral-950 hover:bg-emerald-400"
              >
                {profile.channel.is_live && <span className="h-2 w-2 animate-pulse rounded-full bg-red-600" />}
                {profile.channel.is_live ? t("profile.watchLive") : t("profile.viewChannel")}
              </Link>
            )}
            {profile.is_owner && (
              <Link
                href="/settings"
                className="flex h-9 items-center rounded-md border border-neutral-700 px-4 text-sm font-semibold text-neutral-200 hover:border-emerald-500"
              >
                {t("profile.edit")}
              </Link>
            )}
          </div>
        </div>
        {profile.bio && (
          <p className="whitespace-pre-line border-t border-neutral-800 px-4 py-4 text-sm text-neutral-300 sm:px-6">
            {profile.bio}
          </p>
        )}
        <dl className="grid grid-cols-3 border-t border-neutral-800 text-center">
          {[
            [t("profile.followers"), num(profile.follower_count)],
            [t("profile.following"), num(profile.following_count)],
            [t("profile.achievements"), num(profile.achievements_unlocked)],
          ].map(([label, value]) => (
            <div key={label} className="px-2 py-3">
              <dt className="text-xs text-neutral-500">{label}</dt>
              <dd className="text-lg font-bold tabular-nums">{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        {/* Niveau */}
        <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
          <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-neutral-400">
            {t("profile.level")}
          </h2>
          <div className="flex items-center gap-4">
            <LevelBadge level={profile.level.level} size={64} />
            <div className="min-w-0 flex-1">
              <p className="text-xl font-bold" style={{ color: accent }}>
                {t(`level.${profile.level.level}`)}
              </p>
              <p className="text-xs text-neutral-400">
                {next
                  ? remaining !== null
                    ? t("level.ladder.toNext", { n: num(remaining), level: t(`level.${next.key}`) })
                    : t("profile.nextLevel", { level: t(`level.${next.key}`) })
                  : t("level.ladder.max")}
              </p>
              {next && (
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-neutral-800">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${profile.level.progress}%`,
                      background: `linear-gradient(90deg, ${accent}, ${next.color})`,
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Badges de don */}
        <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
          <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-neutral-400">
            {t("profile.giftBadges")}
          </h2>
          {profile.supported.length === 0 ? (
            <p className="text-sm text-neutral-500">{t("profile.noGifts")}</p>
          ) : (
            <ul className="space-y-2">
              {profile.supported.map((s) => {
                const tier = giftTierByKey(s.gift_tier);
                return (
                  <li key={s.slug}>
                    <Link
                      href={`/c/${s.slug}`}
                      className="flex items-center gap-3 rounded-lg px-2 py-1.5 hover:bg-neutral-800/60"
                    >
                      <Avatar src={s.avatar_url} name={s.display_name} size={32} />
                      <span className="min-w-0 flex-1 truncate text-sm font-semibold">{s.display_name}</span>
                      {typeof s.total_aura === "number" && (
                        <span className="text-xs tabular-nums text-neutral-400">{num(s.total_aura)} Aura</span>
                      )}
                      {tier && (
                        <span className="flex items-center gap-1.5 text-xs font-bold" style={{ color: tier.color }}>
                          <GiftBadge tier={tier} size={26} />
                          <span className="hidden sm:inline">{t(`gift.tier.${tier.key}`)}</span>
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>

      {/* Succès */}
      <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wider text-neutral-400">
          {t("profile.achievements")} · {profile.achievements_unlocked}
          {profile.is_owner ? ` / ${profile.achievements.length}` : ""}
        </h2>
        {profile.achievements.length === 0 ? (
          <p className="text-sm text-neutral-500">{t("profile.noAchievements")}</p>
        ) : (
          <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            {profile.achievements.map((a) => {
              const { name, description } = achText(t, a);
              return (
                <li
                  key={a.key}
                  title={description}
                  className={`flex items-center gap-3 rounded-xl border border-neutral-800 bg-neutral-950/60 p-3 ${
                    a.unlocked ? "" : "opacity-40 grayscale"
                  }`}
                >
                  <AchievementIcon achievement={a} size={30} />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold">{name}</p>
                    <p className="line-clamp-2 text-[11px] text-neutral-500">{description}</p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </main>
  );
}
