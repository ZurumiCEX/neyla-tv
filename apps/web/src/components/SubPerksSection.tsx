"use client";

import { useT } from "@/lib/i18n";

/**
 * Avantages d'abonnement : badge + stickers exclusifs.
 *
 * Le streamer renseigne les URL (en attendant l'upload Cloudflare R2). À défaut,
 * un pack badge + 6 stickers PAR DÉFAUT (SVG inline) est utilisé côté affichage
 * pour que la fonctionnalité soit utilisable immédiatement.
 */
export function SubPerksSection({
  badge,
  setBadge,
  stickers,
  setStickers,
  onSave,
  saving,
  saved,
}: {
  badge: string;
  setBadge: (v: string) => void;
  stickers: string;
  setStickers: (v: string) => void;
  onSave: () => void;
  saving: boolean;
  saved: boolean;
}) {
  const t = useT();
  const stickerList = stickers
    .split("\n")
    .map((s) => s.trim())
    .filter((s) => /^https?:\/\//.test(s));
  const showDefault = stickerList.length === 0;

  return (
    <section className="space-y-4 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
      <div>
        <h2 className="font-semibold">{t("dash.perksTitle")}</h2>
        <p className="mt-1 text-xs text-neutral-400">{t("dash.perksDesc")}</p>
      </div>

      {/* Badge abonné */}
      <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-center">
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wider text-neutral-500">
            {t("dash.perksBadge")}
          </label>
          <input
            type="url"
            value={badge}
            onChange={(e) => setBadge(e.target.value)}
            placeholder="https://… (PNG/SVG/WebP)"
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
          />
          <p className="mt-1 text-[11px] text-neutral-500">{t("dash.perksBadgeHint")}</p>
        </div>
        <BadgePreview url={badge} />
      </div>

      {/* Stickers */}
      <div>
        <label className="mb-1 block text-xs uppercase tracking-wider text-neutral-500">
          {t("dash.perksStickers")}
        </label>
        <textarea
          value={stickers}
          onChange={(e) => setStickers(e.target.value)}
          rows={4}
          placeholder={"https://…/sticker1.png\nhttps://…/sticker2.png"}
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
        />
        <p className="mt-1 text-[11px] text-neutral-500">{t("dash.perksStickersHint")}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {showDefault
            ? DEFAULT_STICKERS.map((d) => <DefaultSticker key={d.key} kind={d.key} />)
            : stickerList.map((url) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  key={url}
                  src={url}
                  alt=""
                  className="h-12 w-12 rounded-lg border border-neutral-800 bg-neutral-900 object-cover"
                />
              ))}
        </div>
        {showDefault && (
          <p className="mt-2 text-[11px] text-neutral-500">{t("dash.perksDefault")}</p>
        )}
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          className="rounded-lg bg-secondary px-4 py-2 text-sm font-semibold text-white hover:bg-secondary-light disabled:opacity-50"
        >
          {saving ? t("common.saving") : t("dash.subSave")}
        </button>
        {saved && <span className="text-sm text-secondary-light">{t("common.saved")}</span>}
      </div>
    </section>
  );
}

function BadgePreview({ url }: { url: string }) {
  if (url && /^https?:\/\//.test(url)) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={url}
        alt=""
        className="h-14 w-14 rounded-lg border border-neutral-800 bg-neutral-900 object-cover"
      />
    );
  }
  // Badge par défaut : étoile dorée sur disque violet (charte).
  return (
    <span
      title="Badge par défaut"
      className="flex h-14 w-14 items-center justify-center rounded-lg border border-neutral-800 bg-secondary/30"
    >
      <svg viewBox="0 0 24 24" width="32" height="32" aria-hidden>
        <path
          d="M12 2l2.6 6.4L21 9l-5 4.5L17.5 21 12 17.5 6.5 21 8 13.5 3 9l6.4-.6L12 2z"
          fill="#FFC81E"
          stroke="#fff"
          strokeWidth="0.6"
        />
      </svg>
    </span>
  );
}

const DEFAULT_STICKERS: { key: string }[] = [
  { key: "heart" },
  { key: "fire" },
  { key: "trophy" },
  { key: "rocket" },
  { key: "thumbsup" },
  { key: "smile" },
];

function DefaultSticker({ kind }: { kind: string }) {
  const map: Record<string, string> = {
    heart: "❤️",
    fire: "🔥",
    trophy: "🏆",
    rocket: "🚀",
    thumbsup: "👍",
    smile: "😄",
  };
  return (
    <span
      title="Sticker par défaut"
      className="flex h-12 w-12 items-center justify-center rounded-lg border border-neutral-800 bg-neutral-900 text-2xl"
      aria-hidden
    >
      {map[kind] ?? "✨"}
    </span>
  );
}
