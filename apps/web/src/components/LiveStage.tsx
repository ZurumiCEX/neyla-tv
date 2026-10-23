"use client";

import { HlsPlayer } from "@/components/HlsPlayer";
import { useLiveStatus } from "@/lib/use-live-status";

/** Lecteur de la page chaîne : bascule automatiquement hors ligne ↔ direct. */
export function LiveStage({
  slug,
  src,
  poster,
  initialLive,
  className,
}: {
  slug: string;
  src: string;
  poster?: string;
  initialLive: boolean;
  className?: string;
}) {
  const { isLive } = useLiveStatus(slug, initialLive);
  return <HlsPlayer src={src} poster={poster} isLive={isLive} className={className} />;
}
