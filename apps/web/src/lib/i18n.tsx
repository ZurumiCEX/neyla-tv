"use client";

// i18n légère côté client : contexte React + dictionnaires FR/EN/PT.
// Locale persistée en localStorage (+ cookie pour cohérence). Pas de préfixe
// d'URL. Les clés non traduites retombent sur la clé brute (FR par défaut).

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

export type Locale = "fr" | "en" | "pt";
export const LOCALES: { code: Locale; label: string }[] = [
  { code: "fr", label: "Français" },
  { code: "en", label: "English" },
  { code: "pt", label: "Português" },
];

type Dict = Record<string, string>;

const FR: Dict = {
  "nav.browse": "Parcourir",
  "nav.becomeStreamer": "Devenir streamer",
  "nav.dashboard": "Dashboard",
  "nav.myChannel": "Ma chaîne",
  "nav.aura": "Aura",
  "nav.invite": "Inviter",
  "nav.achievements": "Succès",
  "nav.inbox": "Messages",
  "nav.settings": "Paramètres",
  "nav.admin": "Admin",
  "nav.logout": "Déconnexion",
  "nav.login": "Connexion",
  "nav.register": "S'inscrire",
  "nav.search": "Rechercher une chaîne ou un jeu…",
  "side.home": "Accueil",
  "side.browse": "Parcourir",
  "side.following": "Suivis",
  "side.noFollows": "Aucune chaîne suivie.",
  "auth.loginTitle": "Connexion",
  "auth.registerTitle": "Créer un compte",
  "auth.email": "Email",
  "auth.username": "Username",
  "auth.password": "Mot de passe",
  "auth.passwordHint": "Mot de passe (10+ caractères)",
  "auth.signin": "Se connecter",
  "auth.signup": "S'inscrire",
  "auth.noAccount": "Pas de compte ?",
  "auth.haveAccount": "Déjà un compte ?",
};

const EN: Dict = {
  "nav.browse": "Browse",
  "nav.becomeStreamer": "Become a streamer",
  "nav.dashboard": "Dashboard",
  "nav.myChannel": "My channel",
  "nav.aura": "Aura",
  "nav.invite": "Invite",
  "nav.achievements": "Achievements",
  "nav.inbox": "Messages",
  "nav.settings": "Settings",
  "nav.admin": "Admin",
  "nav.logout": "Log out",
  "nav.login": "Log in",
  "nav.register": "Sign up",
  "nav.search": "Search a channel or a game…",
  "side.home": "Home",
  "side.browse": "Browse",
  "side.following": "Following",
  "side.noFollows": "No channel followed yet.",
  "auth.loginTitle": "Log in",
  "auth.registerTitle": "Create an account",
  "auth.email": "Email",
  "auth.username": "Username",
  "auth.password": "Password",
  "auth.passwordHint": "Password (10+ characters)",
  "auth.signin": "Log in",
  "auth.signup": "Sign up",
  "auth.noAccount": "No account?",
  "auth.haveAccount": "Already have an account?",
};

const PT: Dict = {
  "nav.browse": "Explorar",
  "nav.becomeStreamer": "Tornar-se streamer",
  "nav.dashboard": "Painel",
  "nav.myChannel": "Meu canal",
  "nav.aura": "Aura",
  "nav.invite": "Convidar",
  "nav.achievements": "Conquistas",
  "nav.inbox": "Mensagens",
  "nav.settings": "Configurações",
  "nav.admin": "Admin",
  "nav.logout": "Sair",
  "nav.login": "Entrar",
  "nav.register": "Registar",
  "nav.search": "Pesquisar um canal ou jogo…",
  "side.home": "Início",
  "side.browse": "Explorar",
  "side.following": "Seguindo",
  "side.noFollows": "Nenhum canal seguido.",
  "auth.loginTitle": "Entrar",
  "auth.registerTitle": "Criar uma conta",
  "auth.email": "Email",
  "auth.username": "Username",
  "auth.password": "Palavra-passe",
  "auth.passwordHint": "Palavra-passe (10+ caracteres)",
  "auth.signin": "Entrar",
  "auth.signup": "Registar",
  "auth.noAccount": "Sem conta?",
  "auth.haveAccount": "Já tem conta?",
};

const DICTS: Record<Locale, Dict> = { fr: FR, en: EN, pt: PT };

type I18nState = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
};

const I18nContext = createContext<I18nState | null>(null);

export function useI18n(): I18nState {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n doit être utilisé sous <I18nProvider>");
  return ctx;
}

/** Raccourci : retourne uniquement la fonction de traduction. */
export function useT(): (key: string) => string {
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
    (key: string) => DICTS[locale][key] ?? DICTS.fr[key] ?? key,
    [locale],
  );

  const value = useMemo<I18nState>(() => ({ locale, setLocale, t }), [locale, setLocale, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
