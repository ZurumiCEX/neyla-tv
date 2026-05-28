"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type AdminUser = {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  date_joined: string;
};

type Page = { count: number; results: AdminUser[] };

const ROLES = ["user", "support", "moderator", "admin"];

export default function AdminUsersPage() {
  const t = useT();
  const { authFetch } = useAuth();
  const [rows, setRows] = useState<AdminUser[]>([]);
  const [q, setQ] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (roleFilter) params.set("role", roleFilter);
    try {
      const data = await authFetch<Page>(`/api/admin/users?${params.toString()}`);
      setRows(data.results);
    } catch {
      setError(t("common.loadError"));
    }
  }, [authFetch, q, roleFilter, t]);

  useEffect(() => {
    load();
  }, [load]);

  async function changeRole(id: number, role: string) {
    try {
      await authFetch(`/api/admin/users/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ role }),
      });
      load();
    } catch {
      setError(t("admin.users.changeError"));
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t("admin.users.search")}
          className="flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-emerald-500"
        />
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-emerald-500"
        >
          <option value="">{t("admin.users.allRoles")}</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="text-sm text-red-300">{error}</p>}

      <div className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/60">
        <table className="w-full text-left text-sm">
          <thead className="bg-neutral-900/80 text-xs uppercase tracking-wider text-neutral-500">
            <tr>
              <th className="px-4 py-3">{t("admin.users.colUser")}</th>
              <th className="px-4 py-3">{t("admin.users.colEmail")}</th>
              <th className="px-4 py-3">{t("admin.users.colRole")}</th>
              <th className="px-4 py-3">{t("admin.users.colJoined")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((u) => (
              <tr key={u.id} className="border-t border-neutral-800/60 hover:bg-neutral-800/30">
                <td className="px-4 py-2.5 text-neutral-200">@{u.username}</td>
                <td className="px-4 py-2.5 text-neutral-400">{u.email}</td>
                <td className="px-4 py-2.5">
                  <select
                    value={u.role}
                    onChange={(e) => changeRole(u.id, e.target.value)}
                    className="rounded-lg border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs text-neutral-100 outline-none focus:border-emerald-500"
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-2.5 text-neutral-500">
                  {new Date(u.date_joined).toLocaleDateString("fr-FR")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && !error && (
          <p className="p-6 text-sm text-neutral-500">{t("admin.users.empty")}</p>
        )}
      </div>
    </div>
  );
}
