"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

// Chaque onglet déclare les rôles autorisés (l'admin a accès à tout).
const TABS: { href: string; labelKey: string; roles: string[] }[] = [
  { href: "/console/dashboard", labelKey: "admin.tab.dashboard", roles: ["admin"] },
  { href: "/console/monitoring", labelKey: "admin.tab.monitoring", roles: ["admin"] },
  { href: "/console/transactions", labelKey: "admin.tab.transactions", roles: ["admin"] },
  { href: "/console/fees", labelKey: "admin.tab.fees", roles: ["admin"] },
  { href: "/console/users", labelKey: "admin.tab.users", roles: ["admin"] },
  { href: "/console/reports", labelKey: "admin.tab.reports", roles: ["admin", "moderator"] },
  { href: "/console/safety", labelKey: "admin.tab.safety", roles: ["admin", "moderator"] },
  { href: "/console/messages", labelKey: "admin.tab.messages", roles: ["admin", "support"] },
  { href: "/console/analytics", labelKey: "admin.tab.analytics", roles: ["admin"] },
];

const STAFF_ROLES = ["admin", "moderator", "support"];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const t = useT();
  const { user, loading } = useAuth();

  // Accès si rôle interne OU compte staff/superuser Django (is_staff).
  const isStaff = !!user && (STAFF_ROLES.includes(user.role) || user.is_staff);
  // Un compte staff sans rôle interne explicite est traité comme admin.
  const effectiveRole = user
    ? STAFF_ROLES.includes(user.role)
      ? user.role
      : user.is_staff
        ? "admin"
        : user.role
    : "";

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
    } else if (!(STAFF_ROLES.includes(user.role) || user.is_staff)) {
      router.replace("/");
    }
  }, [loading, user, router]);

  if (loading || !isStaff) {
    return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;
  }

  const visibleTabs = TABS.filter((tab) => tab.roles.includes(effectiveRole));

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <h1 className="mb-4 text-2xl font-bold">{t("admin.title")}</h1>
      <nav className="mb-6 flex flex-wrap gap-2 border-b border-neutral-800 pb-3">
        {visibleTabs.map((tab) => {
          const active = pathname === tab.href;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${
                active
                  ? "bg-emerald-500 text-neutral-950"
                  : "text-neutral-300 hover:bg-neutral-800"
              }`}
            >
              {t(tab.labelKey)}
            </Link>
          );
        })}
      </nav>
      {children}
    </div>
  );
}
