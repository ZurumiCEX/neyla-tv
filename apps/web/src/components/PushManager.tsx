"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

function urlBase64ToUint8Array(base64: string): Uint8Array {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const b64 = (base64 + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(b64);
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

type State = "loading" | "unsupported" | "unconfigured" | "off" | "on" | "blocked" | "error";

export function PushManager() {
  const t = useT();
  const { authFetch } = useAuth();
  const [state, setState] = useState<State>("loading");
  const [busy, setBusy] = useState(false);
  const [publicKey, setPublicKey] = useState("");

  const init = useCallback(async () => {
    if (
      typeof window === "undefined" ||
      !("serviceWorker" in navigator) ||
      !("PushManager" in window)
    ) {
      setState("unsupported");
      return;
    }
    let key = "";
    try {
      key = (await authFetch<{ public_key: string }>("/api/notifications/push/key")).public_key;
    } catch {
      setState("unconfigured");
      return;
    }
    if (!key) {
      setState("unconfigured");
      return;
    }
    setPublicKey(key);
    if (Notification.permission === "denied") {
      setState("blocked");
      return;
    }
    try {
      // Enregistre le service worker d'abord : sinon l'état « activé » n'est pas lisible.
      const reg = await navigator.serviceWorker.register("/sw.js");
      const existing = await reg.pushManager.getSubscription();
      setState(existing ? "on" : "off");
    } catch {
      setState("error");
    }
  }, [authFetch]);

  useEffect(() => {
    init();
  }, [init]);

  async function enable() {
    setBusy(true);
    try {
      const reg = await navigator.serviceWorker.register("/sw.js");
      await navigator.serviceWorker.ready;
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        setState(permission === "denied" ? "blocked" : "off");
        return;
      }
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey),
      });
      const json = sub.toJSON() as { endpoint?: string; keys?: Record<string, string> };
      await authFetch("/api/notifications/push/subscribe", {
        method: "POST",
        body: JSON.stringify({ endpoint: json.endpoint, keys: json.keys }),
      });
      setState("on");
    } catch {
      setState("error");
    } finally {
      setBusy(false);
    }
  }

  async function disable() {
    setBusy(true);
    try {
      const reg = await navigator.serviceWorker.getRegistration();
      const sub = reg ? await reg.pushManager.getSubscription() : null;
      if (sub) {
        await authFetch("/api/notifications/push/unsubscribe", {
          method: "POST",
          body: JSON.stringify({ endpoint: sub.endpoint }),
        });
        await sub.unsubscribe();
      }
      setState("off");
    } catch {
      setState("error");
    } finally {
      setBusy(false);
    }
  }

  if (state === "loading" || state === "unconfigured") return null;

  return (
    <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
      <h2 className="mb-2 font-semibold">{t("push.title")}</h2>
      <p className="mb-4 text-sm text-neutral-400">{t("push.desc")}</p>
      {state === "unsupported" && (
        <p className="text-sm text-neutral-500">{t("push.unsupported")}</p>
      )}
      {state === "blocked" && <p className="text-sm text-amber-300">{t("push.blocked")}</p>}
      {state === "error" && <p className="mb-3 text-sm text-red-300">{t("push.error")}</p>}
      {(state === "off" || state === "error") && (
        <button
          type="button"
          onClick={enable}
          disabled={busy}
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          {t("push.enable")}
        </button>
      )}
      {state === "on" && (
        <button
          type="button"
          onClick={disable}
          disabled={busy}
          className="rounded-lg border border-neutral-700 px-4 py-2 text-sm hover:border-red-500/50 hover:text-red-300 disabled:opacity-50"
        >
          {t("push.disable")}
        </button>
      )}
    </section>
  );
}
