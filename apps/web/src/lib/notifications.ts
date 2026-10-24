"use client";

// Notifications : type partagé, texte affiché (cloche + boîte de réception)
// et synchronisation du compteur « non lus » entre les deux.

export type Notif = {
  id: number;
  type: string;
  payload: Record<string, string | number | boolean | undefined>;
  read_at: string | null;
  created_at: string;
};

export type NotifPage = { results: Notif[]; unread: number; next_before: number | null };

type TFn = (key: string, params?: Record<string, string | number>) => string;

const str = (v: unknown) => (v === undefined || v === null ? "" : String(v));

/** Texte et lien d'une notification. */
export function describeNotif(n: Notif, t: TFn): { text: string; href?: string; icon: string } {
  const p = n.payload;
  const user = str(p.username);
  switch (n.type) {
    case "live_started":
      return {
        icon: "🔴",
        text: t("notif.live", { name: str(p.display_name || p.username || p.slug) }),
        href: `/c/${str(p.slug)}`,
      };
    case "new_follower":
      return {
        icon: "💛",
        text: t("notif.follower", { user }),
        href: user ? `/u/${user}` : undefined,
      };
    case "subscription":
      return p.gifted
        ? {
            icon: "🎁",
            text: t("notif.giftedTo", { gifter: str(p.gifter), user }),
            href: "/dashboard",
          }
        : { icon: "⭐", text: t("notif.subscription", { user }), href: "/dashboard" };
    case "subscription_gift":
      return {
        icon: "🎁",
        text: t("notif.gifted", { user: str(p.gifter), channel: str(p.channel) }),
        href: p.channel ? `/c/${str(p.channel)}` : undefined,
      };
    case "tip_received":
      return { icon: "💸", text: t("notif.tip", { user, n: str(p.aura) }), href: "/dashboard" };
    case "achievement":
      return {
        icon: str(p.icon) || "🏆",
        text: t("notif.achievement", { name: str(p.name) }),
        href: "/achievements",
      };
    case "support_message":
      return { icon: "✉️", text: t("notif.support", { title: str(p.title) }), href: "/inbox" };
    case "application_decided":
      return {
        icon: p.status === "approved" ? "✅" : "📝",
        text: p.status === "approved" ? t("notif.appApproved") : t("notif.appRejected"),
        href: "/dashboard",
      };
    default:
      return { icon: "🔔", text: t("notif.title") };
  }
}

const EVENT = "neyla:notifications";
export type NotifSync = { unread?: number; readIds?: number[]; delta?: number };

/** Annonce un changement (compteur absolu, ids lus, ou variation du compteur). */
export function publishNotifs(detail: NotifSync): void {
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent(EVENT, { detail }));
}

export function onNotifs(handler: (detail: NotifSync) => void): () => void {
  const fn = (e: Event) => handler((e as CustomEvent<NotifSync>).detail);
  window.addEventListener(EVENT, fn);
  return () => window.removeEventListener(EVENT, fn);
}
