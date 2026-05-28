"use client";

// i18n légère côté client : contexte React au-dessus des dictionnaires partagés
// (cf. messages.ts). Locale persistée en localStorage (+ cookie pour cohérence
// avec le rendu serveur). Pas de préfixe d'URL.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { DICTS, LOCALES, type Locale, translate, type TParams } from "./messages";

export { LOCALES };
export type { Locale };

type I18nState = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string, params?: TParams) => string;
};

const I18nContext = createContext<I18nState | null>(null);

export function useI18n(): I18nState {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n doit être utilisé sous <I18nProvider>");
  return ctx;
}

/** Raccourci : retourne uniquement la fonction de traduction. */
export function useT(): (key: string, params?: TParams) => string {
  return useI18n().t;
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("fr");

  useEffect(() => {
    const stored = localStorage.getItem("locale") as Locale | null;
    if (stored && stored in DICTS) setLocaleState(stored);
  }, []);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    localStorage.setItem("locale", l);
    document.cookie = `locale=${l};path=/;max-age=31536000`;
  }, []);

  const t = useCallback(
    (key: string, params?: TParams) => translate(locale, key, params),
    [locale],
  );

  const value = useMemo<I18nState>(() => ({ locale, setLocale, t }), [locale, setLocale, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
