"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

type LoginResponse = {
  access: string;
  user: { id: number; email: string; username: string; display_name: string };
};

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [result, setResult] = useState<LoginResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const data = await apiFetch<LoginResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setResult(data);
      // Phase 1 démo : on stocke l'access en mémoire seulement.
      // Le refresh est déjà posé en cookie HttpOnly par le backend.
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? "Échec de la connexion.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-md p-8">
      <h1 className="mb-6 text-2xl font-bold">Connexion</h1>
      <form onSubmit={submit} className="space-y-4">
        <label className="block">
          <span className="mb-1 block text-sm text-neutral-300">Email</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-neutral-100 outline-none focus:border-emerald-500"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-sm text-neutral-300">Mot de passe</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-neutral-100 outline-none focus:border-emerald-500"
          />
        </label>
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          {busy ? "..." : "Se connecter"}
        </button>
      </form>
      {error && <p className="mt-4 text-sm text-red-300">{error}</p>}
      {result && (
        <div className="mt-6 rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-4 text-sm">
          <p className="font-semibold text-emerald-200">Connecté en tant que @{result.user.username}</p>
          <p className="mt-2 break-all text-neutral-400">Access (15min) : {result.access}</p>
          <p className="mt-1 text-neutral-400">Refresh : posé en cookie HttpOnly.</p>
        </div>
      )}
      <p className="mt-6 text-sm text-neutral-400">
        Pas de compte ? <a href="/register" className="text-emerald-300 underline">Inscription</a>
      </p>
    </main>
  );
}
