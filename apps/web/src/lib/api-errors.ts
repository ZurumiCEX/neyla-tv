// Message lisible pour une erreur d'API (réseau, limite de débit, serveur…).

import type { ApiError } from "@/lib/api";

type TFn = (key: string, params?: Record<string, string | number>) => string;

export function apiErrorMessage(err: unknown, t: TFn, fallbackKey: string): string {
  const e = err as Partial<ApiError> & { data?: { detail?: string } | null };
  if (e?.status === 0) return t("errors.network");
  const detail = e?.data && typeof e.data === "object" ? e.data.detail : undefined;
  if (detail) return detail;
  if (e?.status === 429) return t("errors.rateLimited");
  if (typeof e?.status === "number" && e.status >= 500) return t("errors.server");
  return t(fallbackKey);
}
