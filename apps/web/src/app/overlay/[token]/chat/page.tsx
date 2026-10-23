"use client";

// Widget OBS « chat » : affiche les derniers messages du chat de la chaîne sur
// fond transparent. Lecture seule (connexion anonyme), reconnexion automatique
// tant que la chaîne n'est pas en direct.

import { use, useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useTransparentBody, wsBase, type OverlayInfo } from "@/lib/overlay";

type ChatMsg = {
  id: string;
  user: { display_name: string; role: string; is_subscriber: boolean };
  content: string;
  ts: number;
};

const MAX_LINES = 12;
const RETRY_MS = 10_000;

export default function ChatWidget({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [slug, setSlug] = useState<string | null>(null);
  const retry = useRef<ReturnType<typeof setTimeout> | null>(null);
  useTransparentBody();

  useEffect(() => {
    apiFetch<OverlayInfo>(`/api/overlay/${encodeURIComponent(token)}`)
      .then((d) => setSlug(d.slug))
      .catch(() => setSlug(null));
  }, [token]);

  useEffect(() => {
    if (!slug) return;
    let ws: WebSocket | null = null;
    let stopped = false;
    const connect = () => {
      ws = new WebSocket(`${wsBase()}/ws/c/${encodeURIComponent(slug)}/chat`);
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data) as { type: string; msg?: ChatMsg; id?: string };
          if (data.type === "message" && data.msg) {
            const msg = data.msg;
            setMessages((prev) => [...prev, msg].slice(-MAX_LINES));
          } else if (data.type === "delete" && data.id) {
            setMessages((prev) => prev.filter((m) => m.id !== data.id));
          }
        } catch {
          /* message illisible ignoré */
        }
      };
      // Chaîne hors ligne (connexion refusée) ou coupure : on réessaie.
      ws.onclose = () => {
        if (!stopped) retry.current = setTimeout(connect, RETRY_MS);
      };
    };
    connect();
    return () => {
      stopped = true;
      if (retry.current) clearTimeout(retry.current);
      ws?.close();
    };
  }, [slug]);

  return (
    <main className="fixed inset-0 flex flex-col justify-end gap-1.5 bg-transparent p-4">
      {messages.map((m) => (
        <p
          key={m.id}
          className="w-fit max-w-full animate-[chatIn_0.25s_ease-out] rounded-lg bg-black/60 px-3 py-1.5 text-lg leading-snug text-white shadow"
        >
          <span
            className="mr-2 font-bold"
            style={{ color: m.user.is_subscriber ? "#d946ef" : "#FFC81E" }}
          >
            {m.user.display_name}
          </span>
          {m.content}
        </p>
      ))}
      <style>{`@keyframes chatIn{from{opacity:0;transform:translateX(-12px)}to{opacity:1;transform:none}}`}</style>
    </main>
  );
}
