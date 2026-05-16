"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";

export function FollowButton({ username }: { username: string }) {
  const { user, authFetch } = useAuth();
  const [following, setFollowing] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!user || user.username === username) {
      setFollowing(null);
      return;
    }
    let cancelled = false;
    authFetch<{ following: boolean }>(`/api/follows/${username}/status`)
      .then((d) => {
        if (!cancelled) setFollowing(d.following);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [user, username, authFetch]);

  if (!user || user.username === username) return null;

  async function toggle() {
    if (following === null) return;
    setBusy(true);
    try {
      if (following) {
        await authFetch(`/api/follows/${username}`, { method: "DELETE" });
        setFollowing(false);
      } else {
        await authFetch(`/api/follows/${username}`, { method: "POST" });
        setFollowing(true);
      }
    } catch {
      /* ignore */
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={busy || following === null}
      className={`rounded-lg px-3 py-1.5 text-sm font-semibold transition ${
        following
          ? "border border-neutral-700 text-neutral-200 hover:border-red-500 hover:text-red-300"
          : "bg-emerald-500 text-neutral-950 hover:bg-emerald-400"
      } disabled:opacity-50`}
    >
      {following === null ? "…" : following ? "Suivi" : "Suivre"}
    </button>
  );
}
