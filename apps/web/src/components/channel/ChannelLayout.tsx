"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { useT } from "@/lib/i18n";
import { ChevronsLeft } from "lucide-react";

const STORAGE_KEY = "neyla.chat.collapsed";

/**
 * Mise en page de la page chaîne : lecteur + infos à gauche, chat pleine hauteur
 * à droite (repliable, état mémorisé). Sur mobile, le chat passe sous le contenu.
 */
export function ChannelLayout({
  slug,
  isLive,
  stage,
  children,
}: {
  slug: string;
  isLive: boolean;
  stage: React.ReactNode;
  children: React.ReactNode;
}) {
  const t = useT();
  const [collapsed, setCollapsed] = useState(false);
  const asideRef = useRef<HTMLElement | null>(null);

  // Le chat occupe la hauteur visible restante (bandeaux d'annonce compris) ;
  // une fois collé en haut (sticky), il prend tout l'écran.
  useEffect(() => {
    const el = asideRef.current;
    if (!el) return;
    let frame = 0;
    const update = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const top = Math.max(0, el.getBoundingClientRect().top);
        el.style.setProperty("--chat-h", `${window.innerHeight - top}px`);
      });
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    // Les bandeaux (annonce, vérification e-mail) apparaissent après coup.
    const observer = new ResizeObserver(update);
    observer.observe(document.body);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [collapsed]);

  useEffect(() => {
    try {
      setCollapsed(window.localStorage.getItem(STORAGE_KEY) === "1");
    } catch {
      /* stockage indisponible */
    }
  }, []);

  const toggle = useCallback((value: boolean) => {
    setCollapsed(value);
    try {
      window.localStorage.setItem(STORAGE_KEY, value ? "1" : "0");
    } catch {
      /* stockage indisponible */
    }
  }, []);

  return (
    <div className="lg:flex lg:items-start">
      <div className="min-w-0 flex-1">
        <div className="relative bg-black">
          {stage}
          {collapsed && (
            <button
              type="button"
              onClick={() => toggle(false)}
              title={t("chat.expand")}
              aria-label={t("chat.expand")}
              className="absolute right-3 top-3 hidden h-9 items-center gap-1.5 rounded-md bg-neutral-950/80 px-3 text-sm font-semibold text-neutral-100 backdrop-blur hover:bg-neutral-900 lg:flex"
            >
              <ChevronsLeft size={16} aria-hidden />
              {t("chat.title")}
            </button>
          )}
        </div>
        {children}
      </div>
      <aside
        ref={asideRef}
        className={`lg:sticky lg:top-0 lg:h-[var(--chat-h,calc(100vh-57px))] lg:w-[340px] lg:shrink-0 lg:border-l lg:border-neutral-800 ${
          collapsed ? "lg:hidden" : ""
        }`}
      >
        <ChatPanel slug={slug} isLive={isLive} variant="sidebar" onCollapse={() => toggle(true)} />
      </aside>
    </div>
  );
}
