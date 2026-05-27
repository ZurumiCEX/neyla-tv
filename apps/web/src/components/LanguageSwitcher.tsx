"use client";

import { LOCALES, useI18n } from "@/lib/i18n";

export function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();
  return (
    <select
      value={locale}
      onChange={(e) => setLocale(e.target.value as (typeof LOCALES)[number]["code"])}
      aria-label="Langue"
      className="rounded-md border border-neutral-700 bg-neutral-900 px-1.5 py-1 text-xs text-neutral-300 outline-none hover:border-neutral-500"
    >
      {LOCALES.map((l) => (
        <option key={l.code} value={l.code}>
          {l.code.toUpperCase()}
        </option>
      ))}
    </select>
  );
}
