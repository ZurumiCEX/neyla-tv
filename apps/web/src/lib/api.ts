// Client API minimal côté navigateur (Client Components).
// Cible publique : NEXT_PUBLIC_API_URL. Les credentials (cookie refresh) sont inclus.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ApiError = { status: number; data: unknown };

export async function apiFetch<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
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
