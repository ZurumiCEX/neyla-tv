"use client";

import { useEffect, useState } from "react";
import { use } from "react";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";

type Props = { params: Promise<{ token: string }> };

export default function VerifyEmailPage({ params }: Props) {
  const t = useT();
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
        setMessage(e.data?.detail ?? t("verify.fail"));
      });
  }, [token, t]);

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center p-8 text-center">
      <h1 className="mb-4 text-2xl font-bold">{t("verify.title")}</h1>
      {state === "pending" && <p className="text-neutral-400">{t("verify.pending")}</p>}
      {state === "ok" && <p className="text-emerald-300">{message}</p>}
      {state === "ko" && <p className="text-red-300">{message}</p>}
      <a href="/login" className="mt-6 text-emerald-300 underline">
        {t("verify.toLogin")}
      </a>
    </main>
  );
}
