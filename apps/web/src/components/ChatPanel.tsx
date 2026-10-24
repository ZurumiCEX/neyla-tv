"use client";

// Panneau de chat live : WS connect (avec JWT en query param), historique pré-chargé,
// envoi de messages, désactivé si hors-ligne et non-streamer.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { EmojiPicker } from "@/components/EmojiPicker";
import { GiftBadge, giftTierByKey } from "@/components/GiftBadge";
import { LevelBadge } from "@/components/LevelBadge";
import { RoleBadge } from "@/components/RoleBadge";
import Link from "next/link";
import { ChatAuraFooter } from "@/components/channel/ChatAuraFooter";

type ChatMessage = {
  id: string;
  user: {
    username: string;
    display_name: string;
    role?: string;
    is_subscriber?: boolean;
    /** Niveau (Aura dépensée à vie) et badge de don pour CETTE chaîne. */
    level?: string;
    gift_tier?: string | null;
  };
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

// Couleurs de pseudo stables (hash du username), lisibles sur fond sombre.
const NAME_COLORS = [
  "#ffd95e",
  "#7dd3fc",
  "#f9a8d4",
  "#86efac",
  "#c4b5fd",
  "#fdba74",
  "#5eead4",
  "#fca5a5",
  "#a5b4fc",
  "#bef264",
];

export function nameColor(username: string): string {
  let h = 0;
  for (let i = 0; i < username.length; i++) h = (h * 31 + username.charCodeAt(i)) | 0;
  return NAME_COLORS[Math.abs(h) % NAME_COLORS.length];
}

type Props = {
  slug: string;
  isLive: boolean;
  /** `sidebar` : colonne pleine hauteur de la page chaîne ; `card` : bloc encadré. */
  variant?: "card" | "sidebar";
  onCollapse?: () => void;
};

export function ChatPanel({ slug, isLive, variant = "card", onCollapse }: Props) {
  const t = useT();
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

  const modCommand = useCallback((cmd: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ content: cmd }));
  }, []);

  const addEmoji = useCallback((emoji: string) => {
    setInput((v) => (v + emoji).slice(0, 500));
  }, []);

  const placeholder = useMemo(() => {
    if (!canConnect) return t("chat.offline");
    if (!user) return t("chat.loginToChat");
    return t("chat.placeholder");
  }, [canConnect, user, t]);

  const disabled = !canConnect || !user;

  return (
    <section
      className={`flex flex-col bg-neutral-950 ${
        variant === "sidebar"
          ? "h-[70vh] border-t border-neutral-800 lg:h-full lg:border-t-0"
          : "h-[60vh] overflow-hidden rounded-xl border border-neutral-800"
      }`}
      aria-label={t("chat.title")}
    >
      <header className="relative flex h-11 shrink-0 items-center justify-center border-b border-neutral-800 px-3 text-sm">
        {onCollapse && (
          <button
            type="button"
            onClick={onCollapse}
            title={t("chat.collapse")}
            aria-label={t("chat.collapse")}
            className="absolute left-2 hidden h-8 w-8 items-center justify-center rounded-md text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100 lg:flex"
          >
            <CollapseIcon />
          </button>
        )}
        <span className="font-semibold uppercase tracking-wide">{t("chat.title")}</span>
        <span
          className={`absolute right-3 h-2 w-2 rounded-full ${
            canConnect && connected ? "bg-green-400" : "bg-neutral-600"
          }`}
          title={canConnect ? (connected ? t("chat.connected") : t("chat.disconnected")) : ""}
        />
      </header>

      <div
        ref={listRef}
        className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2 text-[13px] leading-6"
      >
        {messages.length === 0 && (
          <p className="py-8 text-center text-xs text-neutral-500">{t("chat.empty")}</p>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className="group -mx-1.5 flex items-start gap-1 break-words rounded px-1.5 hover:bg-neutral-900"
          >
            <span className="min-w-0 flex-1">
              <RoleBadge role={m.user.role} />
              {m.user.is_subscriber && (
                <span
                  className="mr-1 inline-flex h-4 w-4 translate-y-[2px] items-center justify-center rounded-sm bg-emerald-500 text-[10px] font-black text-neutral-950"
                  title={t("chat.subscriber")}
                >
                  ★
                </span>
              )}
              <ChatBadges user={m.user} t={t} />
              <Link
                href={`/u/${m.user.username}`}
                className="chat-name font-bold hover:underline"
                style={{ color: nameColor(m.user.username) }}
              >
                {m.user.display_name || m.user.username}
              </Link>
              <span className="text-neutral-500">: </span>
              <span className="text-neutral-100">{m.content}</span>
            </span>
            {isStreamer && (
              <span className="hidden shrink-0 items-center gap-0.5 group-hover:flex">
                {m.user.username !== user?.username && (
                  <>
                    <ModBtn
                      title={t("chat.mod.timeout")}
                      onClick={() => modCommand(`/timeout ${m.user.username} 10`)}
                    >
                      10m
                    </ModBtn>
                    <ModBtn
                      title="Shadow ban"
                      onClick={() => modCommand(`/shadow ${m.user.username}`)}
                    >
                      SB
                    </ModBtn>
                    <ModBtn
                      title={t("chat.mod.ban")}
                      danger
                      onClick={() => {
                        if (window.confirm(`Bannir définitivement @${m.user.username} ?`)) {
                          modCommand(`/ban ${m.user.username}`);
                        }
                      }}
                    >
                      Ban
                    </ModBtn>
                  </>
                )}
                <ModBtn title={t("chat.mod.delete")} danger onClick={() => deleteMessage(m.id)}>
                  ✕
                </ModBtn>
              </span>
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
        className="shrink-0 space-y-2 border-t border-neutral-800 p-3"
      >
        <div className="flex items-center gap-1 rounded-lg border border-neutral-700 bg-neutral-900 pl-3 pr-1 focus-within:border-emerald-400">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={placeholder}
            disabled={disabled}
            maxLength={500}
            className="h-10 min-w-0 flex-1 bg-transparent text-sm text-neutral-100 outline-none placeholder:text-neutral-500 disabled:opacity-50"
          />
          <EmojiPicker onSelect={addEmoji} disabled={disabled} />
        </div>
        <div className="flex items-center justify-between gap-2">
          <ChatAuraFooter />
          <button
            type="submit"
            disabled={disabled || !input.trim()}
            className="rounded-md bg-emerald-500 px-4 py-1.5 text-sm font-bold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {t("chat.send")}
          </button>
        </div>
      </form>
    </section>
  );
}

/** Badges avant le pseudo : badge de don (cette chaîne) puis niveau (hors débutant). */
function ChatBadges({
  user,
  t,
}: {
  user: ChatMessage["user"];
  t: (key: string, params?: Record<string, string | number>) => string;
}) {
  const gift = giftTierByKey(user.gift_tier);
  const level = user.level && user.level !== "rookie" ? user.level : null;
  if (!gift && !level) return null;
  return (
    <span className="mr-1 inline-flex translate-y-[3px] items-center gap-0.5">
      {gift && (
        <span title={t("gift.tierTitle", { tier: t(`gift.tier.${gift.key}`) })}>
          <GiftBadge tier={gift} size={16} animated={false} />
        </span>
      )}
      {level && (
        <span title={t("level.title", { level: t(`level.${level}`) })}>
          <LevelBadge level={level} size={16} animated={false} />
        </span>
      )}
    </span>
  );
}

function CollapseIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M13 17l5-5-5-5M6 17l5-5-5-5" />
    </svg>
  );
}

function ModBtn({
  title,
  onClick,
  danger,
  children,
}: {
  title: string;
  onClick: () => void;
  danger?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      aria-label={title}
      className={`rounded px-1 text-xs leading-5 text-neutral-500 hover:bg-neutral-800 ${
        danger ? "hover:text-red-400" : "hover:text-amber-300"
      }`}
    >
      {children}
    </button>
  );
}
