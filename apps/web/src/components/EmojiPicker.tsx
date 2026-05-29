"use client";

import { useState } from "react";

const EMOJIS = [
  "😀", "😂", "😍", "😎", "😭", "😡", "👍", "👎",
  "🙏", "🔥", "🎉", "❤️", "💯", "👀", "🤔", "😅",
  "🥳", "😱", "🤝", "💪", "🎮", "🏆", "⚡", "✨",
  "👋", "🙌", "😴", "🤬", "🥶", "👑",
];

export function EmojiPicker({
  onSelect,
  disabled,
}: {
  onSelect: (emoji: string) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        className="rounded-lg border border-neutral-700 px-2 py-1.5 text-sm hover:border-secondary hover:text-secondary-light disabled:opacity-50"
        aria-label="Emojis"
      >
        😊
      </button>
      {open && (
        <div className="absolute bottom-full right-0 mb-2 grid w-56 grid-cols-8 gap-1 rounded-lg border border-neutral-800 bg-neutral-900 p-2 shadow-xl">
          {EMOJIS.map((e) => (
            <button
              key={e}
              type="button"
              onClick={() => {
                onSelect(e);
                setOpen(false);
              }}
              className="rounded text-lg hover:bg-neutral-800"
            >
              {e}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
