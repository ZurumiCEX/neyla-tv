"use client";

import { useMemo } from "react";
import { useI18n } from "@/lib/i18n";

const LOCALE_TAGS = { fr: "fr-FR", en: "en-US", pt: "pt-PT" } as const;

/** Formatage localisé selon la langue choisie (nombres, dates). */
export function useFormat() {
  const { locale } = useI18n();
  return useMemo(() => {
    const tag = LOCALE_TAGS[locale] ?? "fr-FR";
    return {
      tag,
      num: (n: number | null | undefined) => (n ?? 0).toLocaleString(tag),
      date: (iso: string | Date, opts?: Intl.DateTimeFormatOptions) =>
        new Date(iso).toLocaleDateString(tag, opts),
      time: (iso: string | Date, opts?: Intl.DateTimeFormatOptions) =>
        new Date(iso).toLocaleTimeString(tag, opts ?? { hour: "2-digit", minute: "2-digit" }),
    };
  }, [locale]);
}
