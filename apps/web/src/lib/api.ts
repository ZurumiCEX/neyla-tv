// Client API : appels publics + helper côté serveur pour le SSR (Server Components).

const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const INTERNAL_API_URL = process.env.API_URL_INTERNAL ?? PUBLIC_API_URL;

export type ApiError = { status: number; data: unknown };

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
