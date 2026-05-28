"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const TABS: { href: string; label: string }[] = [
  { href: "/admin/dashboard", label: "Tableau de bord" },
  { href: "/admin/transactions", label: "Transactions" },
  { href: "/admin/fees", label: "Commissions" },
  { href: "/admin/users", label: "Utilisateurs" },
  { href: "/admin/analytics", label: "Analytics" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
    } else if (user.role !== "admin") {
      router.replace("/");
    }
  }, [loading, user, router]);

  if (loading || !user || user.role !== "admin") {
    return <main className="p-8 text-neutral-500">Chargement…</main>;
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <h1 className="mb-4 text-2xl font-bold">Administration</h1>
      <nav className="mb-6 flex flex-wrap gap-2 border-b border-neutral-800 pb-3">
        {TABS.map((t) => {
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
