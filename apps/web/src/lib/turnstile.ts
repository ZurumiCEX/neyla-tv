// Helpers Turnstile (Cloudflare). Le widget n'est chargé que si la clé site
// est définie (env `NEXT_PUBLIC_TURNSTILE_SITE_KEY`) — sinon, aucun appel
// réseau ni dépendance externe.

export const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? "";

let loadPromise: Promise<void> | null = null;

export function isTurnstileEnabled(): boolean {
  return !!TURNSTILE_SITE_KEY;
}

export function loadTurnstile(): Promise<void> {
  if (typeof window === "undefined" || !TURNSTILE_SITE_KEY) {
    return Promise.resolve();
  }
  if (loadPromise) return loadPromise;
  loadPromise = new Promise<void>((resolve, reject) => {
    if (
      (window as unknown as { turnstile?: unknown }).turnstile !== undefined
    ) {
      resolve();
      return;
    }
    const s = document.createElement("script");
    s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
    s.async = true;
    s.defer = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("turnstile load failed"));
    document.head.appendChild(s);
  });
  return loadPromise;
}
