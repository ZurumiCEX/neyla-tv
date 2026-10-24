"use client";

import { useEffect, useState } from "react";
import { SubPerksSection } from "@/components/SubPerksSection";
import { Switch, inputCls } from "@/components/dashboard/kit";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type SubTier = {
  price_aura?: number;
  perks?: string[];
  badge_url?: string;
  stickers_urls?: string[];
  is_active?: boolean;
};

/** Palier d'abonnement de la chaîne : prix, avantages, badge, stickers, ouverture. */
export function SubTierSettings() {
  const t = useT();
  const { authFetch } = useAuth();
  const [price, setPrice] = useState("100");
  const [perks, setPerks] = useState("");
  const [badge, setBadge] = useState("");
  const [stickers, setStickers] = useState("");
  const [active, setActive] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    authFetch<SubTier>("/api/streamer/tier")
      .then((tier) => {
        if (typeof tier.price_aura === "number") {
          setPrice(String(tier.price_aura));
          setPerks((tier.perks ?? []).join("\n"));
          setBadge(tier.badge_url ?? "");
          setStickers((tier.stickers_urls ?? []).join("\n"));
          setActive(tier.is_active ?? true);
        }
      })
      .catch(() => undefined)
      .finally(() => setLoaded(true));
  }, [authFetch]);

  async function save() {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      await authFetch("/api/streamer/tier", {
        method: "PUT",
        body: JSON.stringify({
          price_aura: Number(price) || 1,
          perks: perks
            .split("\n")
            .map((p) => p.trim())
            .filter(Boolean),
          badge_url: badge.trim(),
          stickers_urls: stickers
            .split("\n")
            .map((s) => s.trim())
            .filter((s) => /^https?:\/\//.test(s))
            .slice(0, 12),
          is_active: active,
        }),
      });
      setSaved(true);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("dash.tierSaveError"));
    } finally {
      setSaving(false);
    }
  }

  if (!loaded) return null;
  return (
    <div className="space-y-4">
      <section className="space-y-4 rounded-lg border border-neutral-800 bg-neutral-900 p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold">{t("dash.subTitle")}</h2>
            <p className="text-sm text-neutral-400">{t("dash.subDesc")}</p>
          </div>
          <Switch label={t("dash.subOpen")} checked={active} onChange={setActive} />
        </div>
        <label className="block text-sm">
          <span className="mb-1 block font-semibold">{t("dash.subPrice")}</span>
          <input
            type="number"
            min={1}
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className={`${inputCls} max-w-40`}
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-semibold">{t("dash.subPerks")}</span>
          <textarea
            value={perks}
            onChange={(e) => setPerks(e.target.value)}
            rows={3}
            placeholder={t("dash2.perksPlaceholder")}
            className={inputCls}
          />
        </label>
        {error && <p className="text-sm text-red-300">{error}</p>}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={save}
            disabled={saving}
            className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-bold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {saving ? t("common.saving") : t("dash.subSave")}
          </button>
          {saved && <span className="text-sm text-green-400">{t("common.saved")}</span>}
        </div>
      </section>
      <SubPerksSection
        badge={badge}
        setBadge={setBadge}
        stickers={stickers}
        setStickers={setStickers}
        onSave={save}
        saving={saving}
        saved={saved}
      />
    </div>
  );
}
