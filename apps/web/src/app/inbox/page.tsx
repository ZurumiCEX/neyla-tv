"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { InboxView } from "@/components/InboxView";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

export default function InboxPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="mb-6 text-2xl font-bold">{t("inbox.title")}</h1>
      <InboxView />
    </main>
  );
}
