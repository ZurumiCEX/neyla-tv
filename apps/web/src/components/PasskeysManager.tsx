"use client";

import { useCallback, useEffect, useState } from "react";
import { KeyRound, Pencil, Trash2 } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

type Passkey = { id: number; name: string; created_at: string; last_used_at: string | null };

const inputCls =
  "rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-emerald-400";

/** Passkeys du compte : ajout (mot de passe requis), renommage, suppression. */
export function PasskeysManager() {
  const t = useT();
  const { date } = useFormat();
  const { authFetch } = useAuth();
  const [items, setItems] = useState<Passkey[] | null>(null);
  const [supported, setSupported] = useState(true);
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    authFetch<{ results: Passkey[] }>("/api/auth/passkeys")
      .then((d) => setItems(d.results))
      .catch(() => setItems([]));
  }, [authFetch]);

  useEffect(() => {
    load();
    import("@simplewebauthn/browser").then(({ browserSupportsWebAuthn }) =>
      setSupported(browserSupportsWebAuthn()),
    );
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { startRegistration } = await import("@simplewebauthn/browser");
      type Options = Parameters<typeof startRegistration>[0]["optionsJSON"];
      const options = await authFetch<Options>("/api/auth/passkeys/register/options", {
        method: "POST",
        body: JSON.stringify({ password }),
      });
      const credential = await startRegistration({ optionsJSON: options });
      await authFetch("/api/auth/passkeys/register/verify", {
        method: "POST",
        body: JSON.stringify({ credential, name: name || t("security.passkeyDefaultName") }),
      });
      setAdding(false);
      setName("");
      setPassword("");
      load();
    } catch (err) {
      const ex = err as { name?: string; data?: { detail?: string } };
      if (ex.name === "NotAllowedError" || ex.name === "AbortError") {
        setError(t("security.passkeyCancelled"));
      } else {
        setError(ex.data?.detail ?? t("security.passkeyError"));
      }
    } finally {
      setBusy(false);
    }
  }

  async function rename(p: Passkey) {
    const next = window.prompt(t("security.passkeyRename"), p.name);
    if (!next || next === p.name) return;
    await authFetch(`/api/auth/passkeys/${p.id}`, {
      method: "PATCH",
      body: JSON.stringify({ name: next }),
    }).catch(() => null);
    load();
  }

  async function remove(p: Passkey) {
    const pwd = window.prompt(t("security.passkeyDeleteConfirm", { name: p.name }));
    if (!pwd) return;
    try {
      await authFetch(`/api/auth/passkeys/${p.id}`, {
        method: "DELETE",
        body: JSON.stringify({ password: pwd }),
      });
      load();
    } catch (err) {
      const ex = err as { data?: { detail?: string } };
      setError(ex.data?.detail ?? t("security.passkeyError"));
    }
  }

  return (
    <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
      <div className="mb-2 flex items-center gap-2">
        <KeyRound size={18} className="text-emerald-300" aria-hidden />
        <h2 className="font-semibold">{t("security.passkeys")}</h2>
      </div>
      <p className="mb-4 text-sm text-neutral-400">{t("security.passkeysDesc")}</p>
      {!supported && (
        <p className="mb-3 text-sm text-amber-300">{t("security.passkeyUnsupported")}</p>
      )}
      {error && <p className="mb-3 text-sm text-red-300">{error}</p>}

      {items && items.length > 0 && (
        <ul className="mb-4 divide-y divide-neutral-800 rounded-lg border border-neutral-800">
          {items.map((p) => (
            <li key={p.id} className="flex items-center gap-3 px-3 py-2.5 text-sm">
              <KeyRound size={16} className="shrink-0 text-neutral-400" aria-hidden />
              <div className="min-w-0 flex-1">
                <p className="truncate font-semibold">{p.name}</p>
                <p className="text-xs text-neutral-500">
                  {t("security.passkeyAdded", { date: date(p.created_at) })}
                  {p.last_used_at
                    ? ` · ${t("security.passkeyUsed", { date: date(p.last_used_at) })}`
                    : ""}
                </p>
              </div>
              <button
                type="button"
                onClick={() => rename(p)}
                aria-label={t("security.passkeyRename")}
                className="rounded-md p-1.5 text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100"
              >
                <Pencil size={15} />
              </button>
              <button
                type="button"
                onClick={() => remove(p)}
                aria-label={t("security.passkeyDelete")}
                className="rounded-md p-1.5 text-neutral-400 hover:bg-red-500/10 hover:text-red-300"
              >
                <Trash2 size={15} />
              </button>
            </li>
          ))}
        </ul>
      )}

      {adding ? (
        <form onSubmit={add} className="space-y-2">
          <div className="grid gap-2 sm:grid-cols-2">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={60}
              placeholder={t("security.passkeyNamePlaceholder")}
              className={inputCls}
            />
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t("security.currentPassword")}
              required
              className={inputCls}
            />
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={busy || !password}
              className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
            >
              {busy ? "…" : t("security.passkeyCreate")}
            </button>
            <button
              type="button"
              onClick={() => setAdding(false)}
              className="rounded-lg px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-800"
            >
              {t("dash2.cancel")}
            </button>
          </div>
        </form>
      ) : (
        <button
          type="button"
          onClick={() => setAdding(true)}
          disabled={!supported}
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          {t("security.passkeyAdd")}
        </button>
      )}
    </section>
  );
}
