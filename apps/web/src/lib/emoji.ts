// Emojis Fluent 3D (Microsoft, MIT) : correspondance caractère → image locale.

import { FLUENT_EMOJIS } from "@/lib/emoji-data";

export type EmojiCategory = "smileys" | "gestures" | "hearts" | "objects";

// Le sélecteur de variante (U+FE0F) est ignoré : « ❤️ » et « ❤ » donnent la même image.
const norm = (s: string) => s.replace(/️/g, "");

const BY_GLYPH = new Map(FLUENT_EMOJIS.map(([, glyph, file]) => [norm(glyph), file]));

/** URL de l'image Fluent d'un emoji, ou null si absent du jeu embarqué. */
export function emojiSrc(glyph: string): string | null {
  const file = BY_GLYPH.get(norm(glyph));
  return file ? `/emoji/fluent/${file}.png` : null;
}

export const EMOJI_CATEGORIES: { key: EmojiCategory; icon: string; items: string[] }[] = (
  ["smileys", "gestures", "hearts", "objects"] as EmojiCategory[]
).map((key) => {
  const items = FLUENT_EMOJIS.filter(([cat]) => cat === key).map(([, glyph]) => glyph);
  return { key, icon: items[0] ?? "", items };
});

export type EmojiPart = { emoji: string; src: string } | string;

const segmenter =
  typeof Intl !== "undefined" && "Segmenter" in Intl
    ? new Intl.Segmenter(undefined, { granularity: "grapheme" })
    : null;

/** Découpe un texte en morceaux texte / emoji (pour afficher les emojis en image). */
export function splitEmoji(text: string): EmojiPart[] {
  if (!text || !/\p{Extended_Pictographic}/u.test(text)) return [text];
  const graphemes = segmenter
    ? Array.from(segmenter.segment(text), (s) => s.segment)
    : Array.from(text);
  const parts: EmojiPart[] = [];
  let buffer = "";
  for (const g of graphemes) {
    const src = /\p{Extended_Pictographic}/u.test(g) ? emojiSrc(g) : null;
    if (src) {
      if (buffer) parts.push(buffer);
      buffer = "";
      parts.push({ emoji: g, src });
    } else {
      buffer += g;
    }
  }
  if (buffer) parts.push(buffer);
  return parts;
}
