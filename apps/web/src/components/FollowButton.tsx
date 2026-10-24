"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { notifyFollowsChanged } from "@/lib/follow-events";
import { useT } from "@/lib/i18n";
import { Heart } from "lucide-react";

export function FollowButton({ username }: { username: string }) {
  const t = useT();
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
      notifyFollowsChanged();
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
      className={`flex h-9 items-center gap-1.5 rounded-md px-4 text-sm font-semibold transition ${
        following
          ? "border border-neutral-700 text-neutral-200 hover:border-red-500 hover:text-red-300"
          : "bg-emerald-500 text-neutral-950 hover:bg-emerald-400"
      } disabled:opacity-50`}
    >
      <HeartIcon filled={!!following} />
      {following === null ? "…" : following ? t("follow.following") : t("follow.follow")}
    </button>
  );
}

function HeartIcon({ filled }: { filled: boolean }) {
  return <Heart size={15} fill={filled ? "currentColor" : "none"} aria-hidden />;
}
