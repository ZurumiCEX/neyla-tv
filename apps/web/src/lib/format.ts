// Formatage des nombres avec séparateur de milliers (FR : espace insécable fine).
// À utiliser sur toute la plateforme pour les montants (Aura, FCFA, viewers…).

export function fmt(n: number | string | null | undefined): string {
  if (n === null || n === undefined || n === "") return "0";
  const num = typeof n === "string" ? Number(n.replace(/\s/g, "").replace(",", ".")) : n;
  if (Number.isNaN(num)) return String(n);
  return num.toLocaleString("fr-FR");
}

/** Montant en FCFA formaté (ex. « 50 000 FCFA »). */
export function fmtFcfa(n: number | string): string {
  return `${fmt(n)} FCFA`;
}

/** Montant en Aura formaté (ex. « 22 000 Aura »). */
export function fmtAura(n: number | string): string {
  return `${fmt(n)} Aura`;
}
