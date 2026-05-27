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
  is_email_verified: boolean;
  is_staff: boolean;
  is_streamer: boolean;
  role: "user" | "support" | "moderator" | "admin";
};

type AuthState = {
  user: AuthUser | null;
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  authFetch: <T>(path: string, init?: RequestInit) => Promise<T>;
  authUpload: <T>(path: string, formData: FormData) => Promise<T>;
};

const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé sous <AuthProvider>");
  return ctx;
}

type LoginResp = { access: string; user: AuthUser };
type RefreshResp = { access: string };

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const accessRef = useRef<string | null>(null);

  // Sync ref avec state pour usage dans des closures stables.
  useEffect(() => {
    accessRef.current = accessToken;
  }, [accessToken]);

  const refresh = useCallback(async (): Promise<string | null> => {
    try {
      const data = await apiFetch<RefreshResp>("/api/auth/refresh", { method: "POST" });
      setAccessToken(data.access);
      return data.access;
    } catch {
      setAccessToken(null);
      setUser(null);
      return null;
    }
  }, []);

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
          setAccessToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    const data = await apiFetch<LoginResp>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setAccessToken(data.access);
    setUser(data.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiFetch("/api/auth/logout", { method: "POST" });
    } catch {
      // best-effort, on nettoie de toute façon
    }
    setAccessToken(null);
    setUser(null);
  }, []);

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

  const value = useMemo<AuthState>(
    () => ({ user, accessToken, loading, login, logout, authFetch, authUpload }),
    [user, accessToken, loading, login, logout, authFetch, authUpload],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
