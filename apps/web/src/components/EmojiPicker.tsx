"use client";

import { useEffect, useRef, useState } from "react";
import { Emoji } from "@/components/Emoji";
import { EMOJI_CATEGORIES, type EmojiCategory } from "@/lib/emoji";
import { useT } from "@/lib/i18n";

/** Sélecteur d'emojis Fluent 3D par catégorie ; insère le caractère Unicode. */
export function EmojiPicker({
  onSelect,
  disabled,
}: {
  onSelect: (emoji: string) => void;
  disabled?: boolean;
}) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [cat, setCat] = useState<EmojiCategory>("smileys");
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const current = EMOJI_CATEGORIES.find((c) => c.key === cat) ?? EMOJI_CATEGORIES[0];

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        disabled={disabled}
        aria-label={t("emoji.open")}
        title={t("emoji.open")}
        className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-neutral-800 disabled:opacity-50"
      >
        <Emoji emoji="😀" size={20} />
      </button>
      {open && (
        <div className="absolute bottom-full right-0 z-50 mb-2 w-72 rounded-xl border border-neutral-800 bg-neutral-900 shadow-xl">
          <div className="flex border-b border-neutral-800 p-1">
            {EMOJI_CATEGORIES.map((c) => (
              <button
                key={c.key}
                type="button"
                onClick={() => setCat(c.key)}
                aria-label={t(`emoji.cat.${c.key}`)}
                title={t(`emoji.cat.${c.key}`)}
                className={`flex flex-1 items-center justify-center rounded-md py-1.5 ${
                  cat === c.key ? "bg-neutral-800" : "hover:bg-neutral-800/60"
                }`}
              >
                <Emoji emoji={c.icon} size={20} />
              </button>
            ))}
          </div>
          <div className="grid max-h-56 grid-cols-7 gap-1 overflow-y-auto p-2">
            {current.items.map((e) => (
              <button
                key={e}
                type="button"
                onClick={() => {
                  onSelect(e);
                }}
                className="flex h-9 w-9 items-center justify-center rounded-md transition hover:scale-110 hover:bg-neutral-800"
              >
                <Emoji emoji={e} size={26} />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
