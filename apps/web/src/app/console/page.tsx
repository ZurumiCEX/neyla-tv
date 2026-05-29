"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

/** /console (nu) → redirige vers la section adaptée au rôle. */
export default function AdminIndexPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    const dest =
      user.role === "moderator"
        ? "/console/reports"
        : user.role === "support"
          ? "/console/messages"
          : user.role === "admin"
            ? "/console/dashboard"
            : "/";
    router.replace(dest);
  }, [loading, user, router]);

  return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;
}
