"use client";

import Link from "next/link";
import { ProfileAchievements } from "@/components/ProfileAchievements";
import type { AchievementItem } from "@/components/AchievementIcon";
import { SocialLinks } from "@/components/SocialLinks";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

/** Carte « À propos de … » : abonnés, réseaux sociaux, bio et succès. */
export function ChannelAbout({
  name,
  username,
  followers,
  bio,
  socialLinks,
  achievements,
}: {
  name: string;
  username: string;
  followers: number;
  bio: string;
  socialLinks: Record<string, string>;
  achievements: AchievementItem[];
}) {
  const t = useT();
  const { num } = useFormat();
  return (
    <section className="rounded-xl bg-neutral-900 p-4 sm:p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-lg font-bold">{t("channel.about", { name })}</h2>
        <Link
          href={`/u/${username}`}
          className="text-xs font-semibold text-emerald-300 hover:underline"
        >
          {t("profile.view")}
        </Link>
      </div>
      <p className="mt-0.5 text-sm font-semibold text-neutral-400">
        {t("channel.followerCount", { n: num(followers) })}
      </p>
      <div className="mt-3">
        <SocialLinks links={socialLinks} />
      </div>
      {bio && <p className="mt-3 whitespace-pre-line text-sm text-neutral-300">{bio}</p>}
      <ProfileAchievements items={achievements} />
    </section>
  );
}
