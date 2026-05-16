"use client";

import { useEffect, useState } from "react";
import { use } from "react";
import { apiFetch } from "@/lib/api";

type Props = { params: Promise<{ token: string }> };

export default function VerifyEmailPage({ params }: Props) {
  const { token } = use(params);
  const [state, setState] = useState<"pending" | "ok" | "ko">("pending");
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiFetch<{ detail: string }>("/api/auth/email/verify", {
      method: "POST",
      body: JSON.stringify({ token }),
    })
      .then((r) => {
        setState("ok");
        setMessage(r.detail);
      })
      .catch((err) => {
        const e = err as { data?: { detail?: string } };
        setState("ko");
        setMessage(e.data?.detail ?? "Échec de la vérification.");
      });
  }, [token]);

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center p-8 text-center">
      <h1 className="mb-4 text-2xl font-bold">Vérification de l&apos;email</h1>
      {state === "pending" && <p className="text-neutral-400">Vérification en cours…</p>}
      {state === "ok" && <p className="text-emerald-300">{message}</p>}
      {state === "ko" && <p className="text-red-300">{message}</p>}
      <a href="/login" className="mt-6 text-emerald-300 underline">
        Aller à la connexion
      </a>
    </main>
  );
}
