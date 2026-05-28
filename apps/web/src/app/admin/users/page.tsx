"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";

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
      setError("Chargement impossible.");
    }
  }, [authFetch, q, roleFilter]);

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
      setError("Modification impossible.");
    }
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Rechercher…"
          className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm"
        />
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm"
        >
          <option value="">Tous les rôles</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="mb-3 text-sm text-red-300">{error}</p>}

      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase tracking-wider text-neutral-500">
          <tr>
            <th className="pb-2">Utilisateur</th>
            <th className="pb-2">Email</th>
            <th className="pb-2">Rôle</th>
            <th className="pb-2">Inscrit</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((u) => (
            <tr key={u.id} className="border-t border-neutral-800/60">
              <td className="py-2 text-neutral-200">@{u.username}</td>
              <td className="py-2 text-neutral-400">{u.email}</td>
              <td className="py-2">
                <select
                  value={u.role}
                  onChange={(e) => changeRole(u.id, e.target.value)}
                  className="rounded-lg border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs text-neutral-100"
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </td>
              <td className="py-2 text-neutral-500">
                {new Date(u.date_joined).toLocaleDateString("fr-FR")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && !error && (
        <p className="mt-4 text-sm text-neutral-500">Aucun utilisateur.</p>
      )}
    </div>
  );
}
