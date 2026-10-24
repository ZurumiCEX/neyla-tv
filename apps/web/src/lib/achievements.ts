import type { AchievementItem } from "@/components/AchievementIcon";

type TFn = (key: string, params?: Record<string, string | number>) => string;

/** Nom / description traduits d'un succès, avec repli sur le texte de l'API. */
export function achText(t: TFn, a: Pick<AchievementItem, "key" | "name" | "description">) {
  const nameKey = `ach.${a.key}.name`;
  const descKey = `ach.${a.key}.desc`;
  const name = t(nameKey);
  const desc = t(descKey);
  return {
    name: name === nameKey ? a.name : name,
    description: desc === descKey ? (a.description ?? "") : desc,
  };
}
