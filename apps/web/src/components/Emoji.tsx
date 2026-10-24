import { emojiSrc, splitEmoji } from "@/lib/emoji";

/** Un emoji en image Fluent 3D (repli sur le caractère s'il n'est pas embarqué). */
export function Emoji({
  emoji,
  size = 20,
  className = "",
}: {
  emoji: string;
  size?: number;
  className?: string;
}) {
  const src = emojiSrc(emoji);
  if (!src) {
    return (
      <span aria-hidden style={{ fontSize: size * 0.85, lineHeight: 1 }} className={className}>
        {emoji}
      </span>
    );
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={emoji}
      width={size}
      height={size}
      loading="lazy"
      draggable={false}
      className={`inline-block select-none align-[-0.2em] ${className}`}
    />
  );
}

/** Texte dont les emojis connus sont rendus en images Fluent (chat, notifications…). */
export function EmojiText({ text, size = 20 }: { text: string; size?: number }) {
  return (
    <>
      {splitEmoji(text).map((part, i) =>
        typeof part === "string" ? (
          <span key={i}>{part}</span>
        ) : (
          <Emoji key={i} emoji={part.emoji} size={size} />
        ),
      )}
    </>
  );
}
