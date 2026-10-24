// Point d'entrée de la console selon le rôle (partagé Sidebar / ProfileMenu).

type StaffLike = { role: string; is_superuser?: boolean } | null | undefined;

/** Mêmes règles que l'API : rôle interne, ou superutilisateur. */
export function canAccessConsole(user: StaffLike): boolean {
  return Boolean(
    user && (["admin", "moderator", "support"].includes(user.role) || user.is_superuser),
  );
}

export function consoleHref(user: StaffLike): string {
  if (user?.role === "moderator") return "/console/reports";
  if (user?.role === "support") return "/console/messages";
  return "/console/dashboard";
}
