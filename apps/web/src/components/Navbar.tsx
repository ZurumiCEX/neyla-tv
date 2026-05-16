"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export function Navbar() {
  const { user, loading, logout } = useAuth();

  return (
    <nav className="border-b border-neutral-800 bg-neutral-950/90 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-lg font-bold tracking-tight">
          Neyla<span className="text-emerald-400">.tv</span>
        </Link>

        <div className="flex items-center gap-4 text-sm">
          {loading ? (
            <span className="text-neutral-500">…</span>
          ) : user ? (
            <>
              <Link href="/dashboard" className="text-neutral-300 hover:text-emerald-300">
                Dashboard
              </Link>
              <Link
                href={`/c/${user.username}`}
                className="text-neutral-300 hover:text-emerald-300"
              >
                Ma chaîne
              </Link>
              <span className="text-neutral-500">@{user.username}</span>
              <button
                type="button"
                onClick={() => logout()}
                className="rounded-md border border-neutral-700 px-2 py-1 text-neutral-300 hover:border-neutral-500"
              >
                Déconnexion
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-neutral-300 hover:text-emerald-300">
                Connexion
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-emerald-500 px-3 py-1 font-semibold text-neutral-950 hover:bg-emerald-400"
              >
                S&apos;inscrire
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
