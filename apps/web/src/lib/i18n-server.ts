// Traduction côté serveur (composants serveur). Lit le cookie `locale` posé par
// le provider client ; retombe sur FR par défaut.

import { cookies } from "next/headers";

import { DICTS, type Locale, translate, type TParams } from "./messages";

export async function getServerT(): Promise<(key: string, params?: TParams) => string> {
  const store = await cookies();
  const raw = store.get("locale")?.value;
  const locale: Locale = raw && raw in DICTS ? (raw as Locale) : "fr";
  return (key: string, params?: TParams) => translate(locale, key, params);
}
