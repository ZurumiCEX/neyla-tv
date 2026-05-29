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
      className={`flex items-center gap-1.5 rounded-lg px-4 py-1.5 text-sm font-semibold transition ${
        following
          ? "border border-neutral-700 text-neutral-200 hover:border-red-500 hover:text-red-300"
          : "bg-emerald-500 text-neutral-950 hover:bg-emerald-400"
      } disabled:opacity-50`}
    >
      <HeartIcon filled={!!following} />
      {following === null ? "…" : following ? "Suivi" : "Suivre"}
    </button>
  );
}

function HeartIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.6l-1-1a5.5 5.5 0 00-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 000-7.8z" />
    </svg>
  );
}
