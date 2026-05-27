"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const SOCIAL_KEYS = [
  "twitter",
  "youtube",
  "instagram",
  "tiktok",
  "discord",
  "website",
] as const;

type Profile = { display_name: string; avatar_url: string; bio: string };
type MyChannel = { banner_url: string; social_links: Record<string, string> };

export default function SettingsPage() {
  const router = useRouter();
  const { user, loading, authFetch } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [bio, setBio] = useState("");
  const [bannerUrl, setBannerUrl] = useState("");
  const [socials, setSocials] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const me = await authFetch<Profile>("/api/auth/me");
      setDisplayName(me.display_name ?? "");
      setAvatarUrl(me.avatar_url ?? "");
      setBio(me.bio ?? "");
      const channel = await authFetch<MyChannel>("/api/channels/me");
      setBannerUrl(channel.banner_url ?? "");
      setSocials(channel.social_links ?? {});
    } catch {
      setError("Échec du chargement du profil.");
    }
  }, [authFetch]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load();
  }, [loading, user, load, router]);

  async function save() {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await authFetch("/api/auth/me", {
        method: "PATCH",
        body: JSON.stringify({
          display_name: displayName,
          avatar_url: avatarUrl,
          bio,
        }),
      });
      const cleanSocials = Object.fromEntries(
        Object.entries(socials).filter(([, v]) => v.trim()),
      );
      await authFetch("/api/channels/me", {
        method: "PATCH",
        body: JSON.stringify({ banner_url: bannerUrl, social_links: cleanSocials }),
      });
      setMessage("Profil enregistré.");
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? "Échec de l'enregistrement.");
    } finally {
      setSaving(false);
    }
  }

  if (loading || (!user && !error)) {
    return <main className="p-8 text-neutral-500">Chargement…</main>;
  }

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="mb-6 text-2xl font-bold">Paramètres du profil</h1>

      {error && (
        <p className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}
      {message && (
        <p className="mb-4 rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-3 text-sm text-emerald-300">
          {message}
        </p>
      )}

      <section className="space-y-4 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
        <Field label="Nom affiché">
          <Input value={displayName} onChange={setDisplayName} maxLength={60} />
        </Field>
        <Field label="Avatar (URL)">
          <Input value={avatarUrl} onChange={setAvatarUrl} placeholder="https://…" />
        </Field>
        <Field label="Bannière (URL)">
          <Input value={bannerUrl} onChange={setBannerUrl} placeholder="https://…" />
        </Field>
        <Field label="Bio">
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            maxLength={500}
            rows={3}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-emerald-500"
          />
        </Field>

        <div className="border-t border-neutral-800 pt-4">
          <p className="mb-2 text-xs uppercase tracking-wider text-neutral-500">
            Réseaux sociaux
          </p>
          <div className="space-y-2">
            {SOCIAL_KEYS.map((key) => (
              <div key={key} className="flex items-center gap-2">
                <span className="w-24 text-sm capitalize text-neutral-400">{key}</span>
                <Input
                  value={socials[key] ?? ""}
                  onChange={(v) => setSocials((s) => ({ ...s, [key]: v }))}
                  placeholder="https://…"
                />
              </div>
            ))}
          </div>
        </div>

        <button
          type="button"
          onClick={save}
          disabled={saving}
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          {saving ? "Enregistrement…" : "Enregistrer"}
        </button>
      </section>
    </main>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-1 text-xs uppercase tracking-wider text-neutral-500">{label}</p>
      {children}
    </div>
  );
}

function Input({
  value,
  onChange,
  placeholder,
  maxLength,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  maxLength?: number;
}) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      maxLength={maxLength}
      className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-emerald-500"
    />
  );
}
