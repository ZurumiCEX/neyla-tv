"use client";

// Jauge animée de robustesse du mot de passe + liste de critères.
// Indicatif côté client : la validation qui fait foi est celle du serveur
// (longueur ≥ 8, pas trop proche de l'email / du pseudo, pas un mot courant).

import { useT } from "@/lib/i18n";

export const PASSWORD_MIN_LENGTH = 8;

type Check = { key: string; ok: boolean };

export function passwordChecks(pw: string): Check[] {
  return [
    { key: "length", ok: pw.length >= PASSWORD_MIN_LENGTH },
    { key: "case", ok: /[a-z]/.test(pw) && /[A-Z]/.test(pw) },
    { key: "digit", ok: /\d/.test(pw) },
    { key: "symbol", ok: /[^A-Za-z0-9]/.test(pw) },
  ];
}

/** Score 0–4 : longueur obligatoire, puis variété et longueur bonus. */
export function passwordScore(pw: string): number {
  if (!pw) return 0;
  const checks = passwordChecks(pw);
  if (!checks[0].ok) return 1;
  let score = checks.filter((c) => c.ok).length; // 1..4
  if (pw.length >= 14 && score < 4) score += 1;
  if (/^(.)\1+$/.test(pw) || /^(?:0123|1234|abcd|azer|qwer|pass)/i.test(pw)) score = 1;
  return Math.min(score, 4);
}

const COLORS = ["bg-neutral-700", "bg-red-500", "bg-orange-500", "bg-amber-400", "bg-emerald-500"];
const TEXT = [
  "text-neutral-500",
  "text-red-400",
  "text-orange-400",
  "text-amber-300",
  "text-emerald-400",
];

export function PasswordStrength({ password, id }: { password: string; id?: string }) {
  const t = useT();
  const score = passwordScore(password);
  const checks = passwordChecks(password);

  return (
    <div id={id} className="mt-2 space-y-2" aria-live="polite">
      <div
        className="flex gap-1"
        role="meter"
        aria-valuemin={0}
        aria-valuemax={4}
        aria-valuenow={score}
      >
        {[1, 2, 3, 4].map((i) => (
          <span key={i} className="h-1.5 flex-1 overflow-hidden rounded-full bg-neutral-800">
            <span
              className={`block h-full rounded-full transition-all duration-500 ease-out ${
                score >= i ? COLORS[score] : "bg-transparent"
              }`}
              style={{ width: score >= i ? "100%" : "0%" }}
            />
          </span>
        ))}
      </div>
      {password && (
        <p className={`text-xs font-semibold transition-colors ${TEXT[score]}`}>
          {t(`auth.strength.${score}`)}
        </p>
      )}
      <ul className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
        {checks.map((c) => (
          <li
            key={c.key}
            className={`flex items-center gap-1.5 transition-colors ${
              c.ok ? "text-emerald-400" : "text-neutral-500"
            }`}
          >
            <span
              aria-hidden
              className={`inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border text-[9px] transition-all ${
                c.ok
                  ? "scale-100 border-emerald-400 bg-emerald-500/20"
                  : "scale-90 border-neutral-600"
              }`}
            >
              {c.ok ? "✓" : ""}
            </span>
            {t(`auth.rule.${c.key}`, { n: PASSWORD_MIN_LENGTH })}
          </li>
        ))}
      </ul>
    </div>
  );
}
