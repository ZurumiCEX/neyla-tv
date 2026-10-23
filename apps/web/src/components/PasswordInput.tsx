"use client";

import { useId, useState } from "react";
import { useT } from "@/lib/i18n";

type Props = {
  label: string;
  value: string;
  onValueChange: (v: string) => void;
  autoComplete?: "current-password" | "new-password";
  required?: boolean;
  minLength?: number;
  invalid?: boolean;
  describedBy?: string;
};

/** Champ mot de passe avec bouton « œil » pour afficher / masquer la saisie. */
export function PasswordInput({
  label,
  value,
  onValueChange,
  autoComplete = "current-password",
  required,
  minLength,
  invalid,
  describedBy,
}: Props) {
  const t = useT();
  const id = useId();
  const [visible, setVisible] = useState(false);

  return (
    <label htmlFor={id} className="block">
      <span className="mb-1 block text-sm text-neutral-300">{label}</span>
      <span className="relative block">
        <input
          id={id}
          type={visible ? "text" : "password"}
          value={value}
          onChange={(e) => onValueChange(e.target.value)}
          autoComplete={autoComplete}
          required={required}
          minLength={minLength}
          aria-invalid={invalid || undefined}
          aria-describedby={describedBy}
          className={`w-full rounded-lg border bg-neutral-900 py-2 pl-3 pr-11 text-neutral-100 outline-none focus:border-secondary-light ${
            invalid ? "border-red-500/70" : "border-neutral-700"
          }`}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? t("auth.hidePassword") : t("auth.showPassword")}
          aria-pressed={visible}
          title={visible ? t("auth.hidePassword") : t("auth.showPassword")}
          className="absolute inset-y-0 right-0 flex w-10 items-center justify-center rounded-r-lg text-neutral-400 hover:text-neutral-100"
        >
          <EyeIcon off={visible} />
        </button>
      </span>
    </label>
  );
}

function EyeIcon({ off }: { off: boolean }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
      {off && <path d="M3 3l18 18" />}
    </svg>
  );
}
