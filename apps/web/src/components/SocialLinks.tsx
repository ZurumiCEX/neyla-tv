// Liens sociaux d'une chaîne : icône de marque + pseudo extrait de l'URL.

const LABELS: Record<string, string> = {
  twitter: "X",
  x: "X",
  youtube: "YouTube",
  instagram: "Instagram",
  tiktok: "TikTok",
  discord: "Discord",
  facebook: "Facebook",
  website: "Site web",
};

const ICONS: Record<string, string> = {
  x: "M17.8 3h3.1l-6.8 7.7L22 21h-6.2l-4.9-6.4L5.3 21H2.2l7.2-8.3L1.8 3h6.4l4.4 5.8L17.8 3zm-1.1 16.2h1.7L7.4 4.7H5.6l11.1 14.5z",
  youtube:
    "M23 7.2a3 3 0 00-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 001 7.2 31 31 0 00.5 12a31 31 0 00.5 4.8 3 3 0 002.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 002.1-2.1 31 31 0 00.5-4.8 31 31 0 00-.5-4.8zM9.7 15.1V8.9l5.8 3.1-5.8 3.1z",
  instagram:
    "M12 2.2c3.2 0 3.6 0 4.8.1 3.3.1 4.8 1.7 4.9 4.9.1 1.3.1 1.6.1 4.8s0 3.6-.1 4.8c-.1 3.2-1.7 4.8-4.9 4.9-1.3.1-1.6.1-4.8.1s-3.6 0-4.8-.1c-3.3-.1-4.8-1.7-4.9-4.9C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.8C2.4 3.9 3.9 2.4 7.2 2.3 8.4 2.2 8.8 2.2 12 2.2zm0 4.9a4.9 4.9 0 100 9.8 4.9 4.9 0 000-9.8zm0 8.1a3.2 3.2 0 110-6.4 3.2 3.2 0 010 6.4zm5.1-9.4a1.2 1.2 0 100 2.3 1.2 1.2 0 000-2.3z",
  tiktok:
    "M16.6 5.8A4.3 4.3 0 0115.5 3h-3.2v12.4a2.6 2.6 0 11-2.6-2.6c.3 0 .5 0 .8.1V9.6a5.9 5.9 0 105.1 5.8V9.2a7.4 7.4 0 004.3 1.4V7.4a4.3 4.3 0 01-3.3-1.6z",
  discord:
    "M20.3 4.4A19.8 19.8 0 0015.4 3l-.6 1.3a18.3 18.3 0 00-5.6 0L8.6 3a19.7 19.7 0 00-4.9 1.4C.6 9 0 13.6.3 18.1a19.9 19.9 0 006 3l1.3-2.1a12.9 12.9 0 01-2-1l.5-.4a14.2 14.2 0 0012.2 0l.5.4c-.6.4-1.3.7-2 1l1.3 2.1a19.8 19.8 0 006-3c.5-5.2-.8-9.7-3.8-13.7zM8.5 15.3c-1.2 0-2.2-1.1-2.2-2.4s1-2.4 2.2-2.4 2.2 1.1 2.2 2.4-1 2.4-2.2 2.4zm7 0c-1.2 0-2.2-1.1-2.2-2.4s1-2.4 2.2-2.4 2.2 1.1 2.2 2.4-1 2.4-2.2 2.4z",
  facebook:
    "M24 12a12 12 0 10-13.9 11.9v-8.4H7.1V12h3V9.4c0-3 1.8-4.7 4.5-4.7 1.3 0 2.7.2 2.7.2v2.9h-1.5c-1.5 0-2 .9-2 1.9V12h3.4l-.5 3.5h-2.9v8.4A12 12 0 0024 12z",
  website:
    "M12 2a10 10 0 100 20 10 10 0 000-20zm6.9 6h-2.9a15.7 15.7 0 00-1.4-3.6A8 8 0 0118.9 8zM12 4c.8 1.2 1.5 2.5 1.9 4h-3.8c.4-1.5 1.1-2.8 1.9-4zM4.3 14a8.2 8.2 0 010-4h3.4a16.5 16.5 0 000 4H4.3zm.8 2h2.9c.3 1.3.8 2.5 1.4 3.6A8 8 0 015.1 16zM8 8H5.1a8 8 0 014.3-3.6C8.8 5.5 8.4 6.7 8 8zm4 12c-.8-1.2-1.5-2.5-1.9-4h3.8c-.4 1.5-1.1 2.8-1.9 4zm2.3-6H9.7a14.7 14.7 0 010-4h4.6a14.7 14.7 0 010 4zm.3 5.6c.6-1.1 1.1-2.3 1.4-3.6h2.9a8 8 0 01-4.3 3.6zm1.7-5.6a16.5 16.5 0 000-4h3.4a8.2 8.2 0 010 4h-3.4z",
};

/** « https://instagram.com/awa.gaming/ » → « awa.gaming » ; sinon le domaine. */
export function socialHandle(url: string): string {
  try {
    const u = new URL(url);
    const parts = u.pathname.split("/").filter(Boolean);
    const last = parts[parts.length - 1];
    if (last && parts.length <= 2) return decodeURIComponent(last).replace(/^@/, "");
    return u.hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function SocialLinks({ links }: { links?: Record<string, string> | null }) {
  const entries = Object.entries(links ?? {}).filter(([, v]) => v);
  if (entries.length === 0) return null;
  return (
    <ul className="flex flex-wrap gap-x-5 gap-y-2">
      {entries.map(([key, url]) => {
        const iconKey = key === "twitter" ? "x" : key;
        const path = ICONS[iconKey] ?? ICONS.website;
        return (
          <li key={key}>
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              title={LABELS[key] ?? key}
              className="flex items-center gap-2 text-sm font-medium text-neutral-300 hover:text-emerald-300"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                <path d={path} />
              </svg>
              <span>{socialHandle(url)}</span>
            </a>
          </li>
        );
      })}
    </ul>
  );
}
