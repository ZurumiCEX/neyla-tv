"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

// Chaque onglet déclare les rôles autorisés (l'admin a accès à tout).
const TABS: { href: string; label: string; roles: string[] }[] = [
  { href: "/admin/dashboard", label: "Tableau de bord", roles: ["admin"] },
  { href: "/admin/transactions", label: "Transactions", roles: ["admin"] },
  { href: "/admin/fees", label: "Commissions", roles: ["admin"] },
  { href: "/admin/users", label: "Utilisateurs", roles: ["admin"] },
  { href: "/admin/reports", label: "Signalements", roles: ["admin", "moderator"] },
  { href: "/admin/messages", label: "Messagerie", roles: ["admin", "support"] },
  { href: "/admin/analytics", label: "Analytics", roles: ["admin"] },
];

const STAFF_ROLES = ["admin", "moderator", "support"];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, loading } = useAuth();

  const isStaff = !!user && STAFF_ROLES.includes(user.role);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
    } else if (!STAFF_ROLES.includes(user.role)) {
      router.replace("/");
    }
  }, [loading, user, router]);

  if (loading || !isStaff) {
    return <main className="p-8 text-neutral-500">Chargement…</main>;
  }

  const visibleTabs = TABS.filter((t) => t.roles.includes(user.role));

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <h1 className="mb-4 text-2xl font-bold">Administration</h1>
      <nav className="mb-6 flex flex-wrap gap-2 border-b border-neutral-800 pb-3">
        {visibleTabs.map((t) => {
          const active = pathname === t.href;
          return (
            <Link
              key={t.href}
              href={t.href}
              className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${
                active
                  ? "bg-emerald-500 text-neutral-950"
                  : "text-neutral-300 hover:bg-neutral-800"
              }`}
            >
              {t.label}
            </Link>
          );
        })}
      </nav>
      {children}
    </div>
  );
}
