// Client API : appels publics + helper côté serveur pour le SSR (Server Components).

// Côté navigateur : défaut "" = chemin relatif (même origine que la page).
// Sur App Platform, /api est routé vers le service api → pas besoin de figer
// l'URL au build (NEXT_PUBLIC_* n'est pas garanti d'être injecté). En dev,
// NEXT_PUBLIC_API_URL est défini (http://localhost:8000) via .env.
const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";
// Côté serveur (SSR) : URL absolue obligatoire (fetch Node), résolue au runtime.
const INTERNAL_API_URL =
  process.env.API_URL_INTERNAL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ApiError = { status: number; data: unknown };

/** Génère une clé d'idempotence (réutilisée sur retry réseau via les headers). */
export function idempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export async function apiFetch<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${PUBLIC_API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
  const text = await res.text();
  const data = text ? (JSON.parse(text) as unknown) : null;
  if (!res.ok) {
    throw { status: res.status, data } satisfies ApiError;
  }
  return data as T;
}

/** Upload multipart (FormData) : ne PAS poser Content-Type (boundary auto). */
export async function apiUpload<T = unknown>(
  path: string,
  formData: FormData,
  init: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${PUBLIC_API_URL}${path}`, {
    method: "POST",
    ...init,
    credentials: "include",
    body: formData,
  });
  const text = await res.text();
  const data = text ? (JSON.parse(text) as unknown) : null;
  if (!res.ok) {
    throw { status: res.status, data } satisfies ApiError;
  }
  return data as T;
}

/** Appel côté serveur (Server Component) : utilise l'URL interne pour fetch direct. */
export async function apiFetchServer<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${INTERNAL_API_URL}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
  const text = await res.text();
  const data = text ? (JSON.parse(text) as unknown) : null;
  if (!res.ok) {
    throw { status: res.status, data } satisfies ApiError;
  }
  return data as T;
}
