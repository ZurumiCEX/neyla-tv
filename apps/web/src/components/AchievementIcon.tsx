// Rendu d'icône de succès : image (icon_url) si présente, sinon emoji.

export type AchievementItem = {
  key: string;
  name: string;
  description?: string;
  criteria?: string;
  icon: string;
  icon_url?: string;
  unlocked?: boolean;
  awarded_at?: string | null;
};

export function AchievementIcon({
  achievement,
  size = 28,
}: {
  achievement: Pick<AchievementItem, "icon" | "icon_url" | "name">;
  size?: number;
}) {
  if (achievement.icon_url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={achievement.icon_url}
        alt={achievement.name}
        className="rounded-md object-cover"
        style={{ width: size, height: size }}
      />
    );
  }
  return (
    <span style={{ fontSize: size * 0.85, lineHeight: 1 }} aria-hidden>
      {achievement.icon}
    </span>
  );
}
