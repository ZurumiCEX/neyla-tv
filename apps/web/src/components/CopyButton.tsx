"use client";

import { useState } from "react";
import { useT } from "@/lib/i18n";

export function CopyButton({ value, label }: { value: string; label?: string }) {
  const t = useT();
  const [copied, setCopied] = useState(false);

  async function copy() {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard indisponible : on ignore */
    }
  }

  return (
    <button
      type="button"
      onClick={copy}
      disabled={!value}
      className="rounded-md border border-neutral-700 px-2 py-1 text-xs text-neutral-300 hover:border-secondary hover:text-secondary-light disabled:opacity-50"
    >
      {copied ? t("common.copied") : (label ?? t("common.copy"))}
    </button>
  );
}
