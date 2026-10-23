"use client";

// Signal global « la liste des chaînes suivies a changé » (follow / unfollow).
const EVENT = "neyla:follows-changed";

export function notifyFollowsChanged(): void {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(EVENT));
}

export function onFollowsChanged(handler: () => void): () => void {
  window.addEventListener(EVENT, handler);
  return () => window.removeEventListener(EVENT, handler);
}
