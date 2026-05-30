"use client";

import { useEffect, useRef, useState } from "react";
import { useT } from "@/lib/i18n";

type Props = {
  /** URL absolue ou relative (préfixée par `origin` à la volée). */
  path: string;
  /** Titre/texte d'accompagnement pour les partages sociaux. */
  title?: string;
};

/**
 * Bouton de partage : copie du lien interne + cibles réseaux sociaux
 * (X, Facebook, WhatsApp, Telegram) et Web Share API si dispo.
 */
export function ShareButton({ path, title }: Props) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  const url =
    typeof window !== "undefined"
      ? new URL(path, window.location.origin).toString()
      : path;
  const text = title ?? t("share.text");
  const canNativeShare =
    typeof navigator !== "undefined" && typeof navigator.share === "function";

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard indisponible : on ignore */
    }
  }

  async function nativeShare() {
    try {
      await navigator.share({ title: text, text, url });
    } catch {
      /* l'utilisateur a annulé */
    }
  }

  const enc = encodeURIComponent;
  const targets: { key: string; label: string; href: string }[] = [
    {
      key: "x",
      label: t("share.x"),
      href: `https://twitter.com/intent/tweet?text=${enc(text)}&url=${enc(url)}`,
    },
    {
      key: "facebook",
      label: t("share.facebook"),
      href: `https://www.facebook.com/sharer/sharer.php?u=${enc(url)}`,
    },
    {
      key: "whatsapp",
      label: t("share.whatsapp"),
      href: `https://api.whatsapp.com/send?text=${enc(text + " " + url)}`,
    },
    {
      key: "telegram",
      label: t("share.telegram"),
      href: `https://t.me/share/url?url=${enc(url)}&text=${enc(text)}`,
    },
  ];

  return (
    <div ref={ref} className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="rounded-md border border-neutral-700 px-3 py-1.5 text-sm text-neutral-200 hover:border-secondary hover:text-secondary-light"
      >
        {t("share.title")}
      </button>
      {open && (
        <div className="absolute right-0 z-40 mt-2 w-56 overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 shadow-xl">
          <button
            type="button"
            onClick={copy}
            className="block w-full px-3 py-2 text-left text-sm text-neutral-200 hover:bg-neutral-800"
          >
            {copied ? t("share.copied") : t("share.copyLink")}
          </button>
          {canNativeShare && (
            <button
              type="button"
              onClick={nativeShare}
              className="block w-full px-3 py-2 text-left text-sm text-neutral-200 hover:bg-neutral-800"
            >
              {t("share.native")}
            </button>
          )}
          <div className="border-t border-neutral-800" />
          {targets.map((tgt) => (
            <a
              key={tgt.key}
              href={tgt.href}
              target="_blank"
              rel="noopener noreferrer"
              className="block px-3 py-2 text-sm text-neutral-200 hover:bg-neutral-800"
              onClick={() => setOpen(false)}
            >
              {tgt.label}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
