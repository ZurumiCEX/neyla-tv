"use client";

// Panneau de chat live : WS connect (avec JWT en query param), historique pré-chargé,
// envoi de messages, désactivé si hors-ligne et non-streamer.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { EmojiPicker } from "@/components/EmojiPicker";

type ChatMessage = {
  id: string;
  user: { username: string; display_name: string };
  content: string;
  ts: number;
};

type SystemEvent = { type: "system" | "error" | "kicked"; detail: string };

const PUBLIC_API = process.env.NEXT_PUBLIC_API_URL ?? "";

function wsBase(): string {
  if (PUBLIC_API) return PUBLIC_API.replace(/^http/, "ws");
  // Même origine que la page (App Platform route /ws vers l'api).
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${window.location.host}`;
  }
  return "";
}

export function ChatPanel({
  slug,
  isLive,
}: {
  slug: string;
  isLive: boolean;
}) {
  const { user, accessToken } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [system, setSystem] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);

  const isStreamer = user?.username === slug;
  const canConnect = isLive || isStreamer;

  // Historique au mount.
  useEffect(() => {
    apiFetch<{ messages: ChatMessage[] }>(`/api/c/${slug}/chat/history`)
      .then((data) => setMessages(data.messages))
      .catch(() => undefined);
  }, [slug]);

  // Connexion WS.
  useEffect(() => {
    if (!canConnect) return;
    const token = accessToken ?? "";
    const qs = token ? `?token=${encodeURIComponent(token)}` : "";
    const ws = new WebSocket(`${wsBase()}/ws/c/${slug}/chat${qs}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as
          | { type: "message"; msg: ChatMessage }
          | { type: "delete"; id: string }
          | SystemEvent;
        if (data.type === "message") {
          setMessages((prev) => [...prev.slice(-199), data.msg]);
        } else if (data.type === "delete") {
          setMessages((prev) => prev.filter((m) => m.id !== data.id));
        } else {
          setSystem(data.detail);
        }
      } catch {
        /* ignore */
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [slug, accessToken, canConnect]);

  // Auto-scroll vers le bas si l'utilisateur est déjà près du bas.
  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
    if (nearBottom) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const send = useCallback(() => {
    const text = input.trim();
    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ content: text }));
    setInput("");
  }, [input]);

  const deleteMessage = useCallback((id: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ content: `/delete ${id}` }));
  }, []);

  const addEmoji = useCallback((emoji: string) => {
    setInput((v) => (v + emoji).slice(0, 500));
  }, []);

  const placeholder = useMemo(() => {
    if (!canConnect) return "Chat indisponible (chaîne hors-ligne).";
    if (!user) return "Connecte-toi pour discuter.";
    return "Écris ton message…";
  }, [canConnect, user]);

  return (
    <section className="flex h-[60vh] flex-col rounded-xl border border-neutral-800 bg-neutral-900/60">
      <header className="flex items-center justify-between border-b border-neutral-800 px-4 py-2 text-sm">
        <span className="font-semibold">Chat</span>
        <span
          className={`text-xs ${connected ? "text-emerald-300" : "text-neutral-500"}`}
        >
          {canConnect ? (connected ? "connecté" : "déconnecté") : "—"}
        </span>
      </header>

      <div ref={listRef} className="flex-1 space-y-1 overflow-y-auto px-3 py-2 text-sm">
        {messages.length === 0 && (
          <p className="py-8 text-center text-xs text-neutral-500">
            Aucun message pour le moment.
          </p>
        )}
        {messages.map((m) => (
          <div key={m.id} className="group flex items-start gap-1 break-words">
            <span className="min-w-0 flex-1">
              <span className="font-semibold text-emerald-300">
                {m.user.display_name || m.user.username}
              </span>
              <span className="text-neutral-500"> : </span>
              <span className="text-neutral-100">{m.content}</span>
            </span>
            {isStreamer && (
              <button
                type="button"
                onClick={() => deleteMessage(m.id)}
                className="hidden shrink-0 text-xs text-neutral-500 hover:text-red-400 group-hover:block"
                title="Supprimer ce message"
                aria-label="Supprimer"
              >
                ✕
              </button>
            )}
          </div>
        ))}
      </div>

      {system && (
        <div className="border-t border-neutral-800 bg-neutral-900/80 px-3 py-1 text-xs text-amber-300">
          {system}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="flex gap-2 border-t border-neutral-800 p-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder}
          disabled={!canConnect || !user}
          maxLength={500}
          className="flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-1.5 text-sm text-neutral-100 outline-none focus:border-emerald-500 disabled:opacity-50"
        />
        <EmojiPicker onSelect={addEmoji} disabled={!canConnect || !user} />
        <button
          type="submit"
          disabled={!canConnect || !user || !input.trim()}
          className="rounded-lg bg-emerald-500 px-3 py-1.5 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          Envoyer
        </button>
      </form>
    </section>
  );
}
