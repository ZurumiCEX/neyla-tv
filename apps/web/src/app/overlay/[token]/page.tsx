"use client";

import { use, useEffect, useRef, useState } from "react";

type Alert = { kind: "follow" | "tip" | "subscribe" | "test"; actor: string; amount?: number; ts: number };

const PUBLIC_API = process.env.NEXT_PUBLIC_API_URL ?? "";

function wsBase(): string {
  if (PUBLIC_API) return PUBLIC_API.replace(/^http/, "ws");
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${window.location.host}`;
  }
  return "";
}

const ACCENTS: Record<Alert["kind"], string> = {
  follow: "#FFC81E",
  tip: "#3b82f6",
  subscribe: "#d946ef",
  test: "#f59e0b",
};

function headline(a: Alert): string {
  switch (a.kind) {
    case "tip":
      return `${a.actor} a envoyé ${a.amount ?? 0} Aura !`;
    case "subscribe":
      return `${a.actor} vient de s'abonner !`;
    case "test":
      return `Alerte de test — ${a.actor}`;
    default:
      return `${a.actor} te suit !`;
  }
}

export default function OverlayPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);
  const [current, setCurrent] = useState<Alert | null>(null);
  const queue = useRef<Alert[]>([]);
  const showing = useRef(false);

  // Fond transparent pour la capture OBS.
  useEffect(() => {
    const prev = document.body.style.background;
    document.body.style.background = "transparent";
    return () => {
      document.body.style.background = prev;
    };
  }, []);

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

  return (
    <main className="fixed inset-0 flex items-start justify-center bg-transparent p-8">
      {current && (
        <div
          key={current.ts}
          className="animate-[overlayIn_0.4s_ease-out] rounded-2xl border px-8 py-5 text-center shadow-2xl backdrop-blur"
          style={{
            borderColor: ACCENTS[current.kind],
            background: "rgba(10,10,10,0.85)",
            boxShadow: `0 0 40px ${ACCENTS[current.kind]}66`,
          }}
        >
          <p
            className="text-xs font-bold uppercase tracking-widest"
            style={{ color: ACCENTS[current.kind] }}
          >
            {current.kind === "tip"
              ? "Tip"
              : current.kind === "subscribe"
                ? "Nouvel abonné"
                : current.kind === "test"
                  ? "Test"
                  : "Nouveau follower"}
          </p>
          <p className="mt-1 text-2xl font-extrabold text-white">{headline(current)}</p>
        </div>
      )}
      <style>{`@keyframes overlayIn{from{opacity:0;transform:translateY(-20px) scale(0.95)}to{opacity:1;transform:none}}`}</style>
    </main>
  );
}
