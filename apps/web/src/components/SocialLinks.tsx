const LABELS: Record<string, string> = {
  twitter: "Twitter",
  youtube: "YouTube",
  instagram: "Instagram",
  tiktok: "TikTok",
  discord: "Discord",
  website: "Site web",
};

export function SocialLinks({ links }: { links?: Record<string, string> | null }) {
  const entries = Object.entries(links ?? {}).filter(([, v]) => v);
  if (entries.length === 0) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {entries.map(([key, url]) => (
        <a
          key={key}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-full border border-neutral-700 px-3 py-1 text-xs text-neutral-300 hover:border-emerald-500 hover:text-emerald-300"
        >
          {LABELS[key] ?? key}
        </a>
      ))}
    </div>
  );
}
