const ROLE_META: Record<string, { label: string; cls: string }> = {
  admin: { label: "Admin", cls: "bg-red-500/20 text-red-300" },
  moderator: { label: "Mod", cls: "bg-emerald-500/20 text-emerald-300" },
  support: { label: "Support", cls: "bg-sky-500/20 text-sky-300" },
};

export function RoleBadge({ role }: { role?: string }) {
  const meta = role ? ROLE_META[role] : undefined;
  if (!meta) return null;
  return (
    <span
      className={`mr-1 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${meta.cls}`}
    >
      {meta.label}
    </span>
  );
}
