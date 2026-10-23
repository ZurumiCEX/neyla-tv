"use client";

// Contexte d'auth côté navigateur.
// - Access token : en mémoire React seulement (pas de localStorage, anti-XSS).
// - Refresh token : cookie HttpOnly posé par le backend, envoyé automatiquement.
// - Au mount : on tente un /refresh silencieux pour récupérer l'access.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { apiFetch, apiUpload, type ApiError } from "@/lib/api";

export type AuthUser = {
  id: number;
  email: string;
  username: string;
  display_name: string;
  avatar_url: string;
  is_email_verified: boolean;
  is_staff: boolean;
  is_streamer: boolean;
  two_factor_enabled?: boolean;
  role: "user" | "support" | "moderator" | "admin";
};

export type LoginResult = { twoFactorRequired: false } | { twoFactorRequired: true; token: string };

type AuthState = {
  user: AuthUser | null;
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<LoginResult>;
  loginTwoFactor: (token: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
  /** Adopte une session déjà ouverte côté serveur (ex. réponse d'inscription). */
  adoptSession: (access: string, user: AuthUser) => void;
  /** Recharge le profil (ex. après vérification de l'e-mail). */
  reloadUser: () => Promise<void>;
  authFetch: <T>(path: string, init?: RequestInit) => Promise<T>;
  authUpload: <T>(path: string, formData: FormData) => Promise<T>;
};

const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé sous <AuthProvider>");
  return ctx;
}

type LoginResp = { access: string; user: AuthUser } | { two_factor_required: true; token: string };
type RefreshResp = { access: string };

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const accessRef = useRef<string | null>(null);
  const refreshInFlight = useRef<Promise<string | null> | null>(null);

  // Met à jour le ref IMMÉDIATEMENT (pas dans un effet) : les effets des pages
  // enfants s'exécutent avant ceux du provider, et appelleraient sinon l'API
  // sans jeton juste après la connexion.
  const applyAccess = useCallback((token: string | null) => {
    accessRef.current = token;
    setAccessToken(token);
  }, []);

  // Un seul refresh à la fois : le refresh fait tourner le cookie (l'ancien est
  // révoqué), des appels parallèles se révoqueraient mutuellement → déconnexion.
  const refresh = useCallback((): Promise<string | null> => {
    if (refreshInFlight.current) return refreshInFlight.current;
    const run = (async () => {
      try {
        const data = await apiFetch<RefreshResp>("/api/auth/refresh", { method: "POST" });
        applyAccess(data.access);
        return data.access;
      } catch {
        applyAccess(null);
        setUser(null);
        return null;
      } finally {
        refreshInFlight.current = null;
      }
    })();
    refreshInFlight.current = run;
    return run;
  }, [applyAccess]);

  // Bootstrap : tente un refresh silencieux puis charge le profil.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const token = await refresh();
      if (!token || cancelled) {
        setLoading(false);
        return;
      }
      try {
        const me = await apiFetch<AuthUser>("/api/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) {
          applyAccess(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refresh, applyAccess]);

  const login = useCallback(
    async (email: string, password: string): Promise<LoginResult> => {
      const data = await apiFetch<LoginResp>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if ("two_factor_required" in data) {
        return { twoFactorRequired: true, token: data.token };
      }
      applyAccess(data.access);
      setUser(data.user);
      return { twoFactorRequired: false };
    },
    [applyAccess],
  );

  const loginTwoFactor = useCallback(
    async (token: string, code: string) => {
      const data = await apiFetch<{ access: string; user: AuthUser }>("/api/auth/2fa/login", {
        method: "POST",
        body: JSON.stringify({ token, code }),
      });
      applyAccess(data.access);
      setUser(data.user);
    },
    [applyAccess],
  );

  const logout = useCallback(async () => {
    try {
      await apiFetch("/api/auth/logout", { method: "POST" });
    } catch {
      // best-effort, on nettoie de toute façon
    }
    applyAccess(null);
    setUser(null);
  }, [applyAccess]);

  const adoptSession = useCallback(
    (access: string, nextUser: AuthUser) => {
      applyAccess(access);
      setUser(nextUser);
    },
    [applyAccess],
  );

  // Fetch authentifié avec retry auto sur 401 (refresh + replay une fois).
  const authFetch = useCallback(
    async <T,>(path: string, init: RequestInit = {}): Promise<T> => {
      const token = accessRef.current;
      const headers = {
        ...(init.headers ?? {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };
      try {
        return await apiFetch<T>(path, { ...init, headers });
      } catch (err) {
        const e = err as ApiError;
        if (e.status !== 401) throw err;
        const fresh = await refresh();
        if (!fresh) throw err;
        return await apiFetch<T>(path, {
          ...init,
          headers: { ...(init.headers ?? {}), Authorization: `Bearer ${fresh}` },
        });
      }
    },
    [refresh],
  );

  const authUpload = useCallback(
    async <T,>(path: string, formData: FormData): Promise<T> => {
      const token = accessRef.current;
      const headers: Record<string, string> = {};
      if (token) headers.Authorization = `Bearer ${token}`;
      try {
        return await apiUpload<T>(path, formData, { headers });
      } catch (err) {
        const e = err as ApiError;
        if (e.status !== 401) throw err;
        const fresh = await refresh();
        if (!fresh) throw err;
        return await apiUpload<T>(path, formData, {
          headers: { Authorization: `Bearer ${fresh}` },
        });
      }
    },
    [refresh],
  );

  const reloadUser = useCallback(async () => {
    const token = accessRef.current;
    if (!token) return;
    try {
      setUser(
        await apiFetch<AuthUser>("/api/auth/me", { headers: { Authorization: `Bearer ${token}` } }),
      );
    } catch {
      /* profil inchangé */
    }
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      accessToken,
      loading,
      login,
      loginTwoFactor,
      logout,
      adoptSession,
      reloadUser,
      authFetch,
      authUpload,
    }),
    [
      user,
      accessToken,
      loading,
      login,
      loginTwoFactor,
      logout,
      adoptSession,
      reloadUser,
      authFetch,
      authUpload,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
