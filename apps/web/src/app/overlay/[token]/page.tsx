"use client";

import { use, useEffect, useRef, useState } from "react";
import { DonationTierBadge } from "@/components/DonationTierBadge";
import { donationTier } from "@/lib/donation-tiers";
import { fmt } from "@/lib/format";
import { useT } from "@/lib/i18n";
import { useTransparentBody, wsBase } from "@/lib/overlay";

type Alert = {
  kind: "follow" | "tip" | "subscribe" | "gift" | "test";
  actor: string;
  amount?: number;
  ts: number;
};

const ACCENTS: Record<Alert["kind"], string> = {
  follow: "#FFC81E",
  tip: "#3b82f6",
  subscribe: "#d946ef",
  gift: "#ec4899",
  test: "#f59e0b",
};

type TFn = (key: string, params?: Record<string, string | number>) => string;

function headline(a: Alert, t: TFn): string {
  switch (a.kind) {
    case "tip":
      return t("overlay.tip", { actor: a.actor, n: fmt(a.amount ?? 0) });
    case "subscribe":
      return t("overlay.subscribe", { actor: a.actor });
    case "gift":
      return t("overlay.gift", { actor: a.actor });
    case "test":
      return t("overlay.test", { actor: a.actor });
    default:
      return t("overlay.follow", { actor: a.actor });
  }
}

export default function OverlayPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);
  const t = useT();
  const [current, setCurrent] = useState<Alert | null>(null);
  const queue = useRef<Alert[]>([]);
  const showing = useRef(false);

  useTransparentBody();

  useEffect(() => {
    function next() {
      const a = queue.current.shift();
      if (!a) {
        showing.current = false;
        return;
      }
      showing.current = true;
      setCurrent(a);
      setTimeout(() => {
        setCurrent(null);
        setTimeout(next, 400); // laisse l'animation de sortie se jouer
      }, 5000);
    }

    const ws = new WebSocket(`${wsBase()}/ws/overlay/${encodeURIComponent(token)}`);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as { type: string; alert?: Alert };
        if (data.type === "alert" && data.alert) {
          queue.current.push(data.alert);
          if (!showing.current) next();
        }
      } catch {
        /* ignore */
      }
    };
    return () => ws.close();
  }, [token]);

  const tipTier = current?.kind === "tip" ? donationTier(current.amount ?? 0) : null;
  const accent = tipTier ? tipTier.color : current ? ACCENTS[current.kind] : "#FFC81E";

  return (
    <main className="fixed inset-0 flex items-start justify-center bg-transparent p-8">
      {current && (
        <div
          key={current.ts}
          className="animate-[overlayIn_0.4s_ease-out] flex flex-col items-center rounded-2xl border px-8 py-5 text-center shadow-2xl backdrop-blur"
          style={{
            borderColor: accent,
            background: "rgba(10,10,10,0.85)",
            boxShadow: `0 0 40px ${accent}66`,
          }}
        >
          {tipTier && <DonationTierBadge tier={tipTier} size={72} />}
          <p className="mt-2 text-xs font-bold uppercase tracking-widest" style={{ color: accent }}>
            {current.kind === "tip"
              ? tipTier
                ? tipTier.name
                : t("overlay.label.tip")
              : t(`overlay.label.${current.kind}`)}
          </p>
          <p className="mt-1 text-2xl font-extrabold text-white">{headline(current, t)}</p>
        </div>
      )}
      <style>{`@keyframes overlayIn{from{opacity:0;transform:translateY(-20px) scale(0.95)}to{opacity:1;transform:none}}`}</style>
    </main>
  );
}
