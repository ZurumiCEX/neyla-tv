"use client";

import Link from "next/link";
import { useT } from "@/lib/i18n";

type Col = { titleKey: string; links: { label: string; href: string }[] };

export function Footer() {
  const t = useT();
  const year = new Date().getFullYear();

  const cols: Col[] = [
    {
      titleKey: "footer.platform",
      links: [
        { label: t("nav.browse"), href: "/parcourir" },
        { label: t("side.following"), href: "/suivis" },
        { label: t("nav.becomeStreamer"), href: "/become-streamer" },
      ],
    },
    {
      titleKey: "footer.product",
      links: [
        { label: t("nav.wallet"), href: "/wallet" },
        { label: t("nav.achievements"), href: "/achievements" },
        { label: t("guides.title"), href: "/guides" },
        { label: t("footer.charity"), href: "/charity" },
        { label: t("footer.status"), href: "/statut" },
      ],
    },
    {
      titleKey: "footer.support",
      links: [
        { label: t("guides.title"), href: "/guides" },
        { label: t("nav.inbox"), href: "/inbox" },
        { label: t("nav.settings"), href: "/settings" },
      ],
    },
    {
      titleKey: "footer.legal",
      links: [
        { label: t("footer.terms"), href: "/terms" },
        { label: t("footer.privacy"), href: "/privacy" },
        { label: t("footer.about"), href: "/about" },
        { label: t("footer.contact"), href: "/contact" },
      ],
    },
  ];

  return (
    <footer className="mt-12 border-t border-neutral-800 bg-neutral-950">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-2 md:grid-cols-4">
          {cols.map((c) => (
            <div key={c.titleKey}>
              <p className="mb-3 text-sm font-bold text-neutral-100">{t(c.titleKey)}</p>
              <ul className="space-y-2">
                {c.links.map((l) => (
                  <li key={l.href + l.label}>
                    <Link
                      href={l.href}
                      className="text-sm text-neutral-400 transition hover:text-secondary-light"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Logo centré — agrandi ×2 environ (text-3xl → text-7xl) */}
        <div className="my-12 flex justify-center">
          <Link
            href="/"
            className="text-6xl font-extrabold tracking-tight sm:text-7xl"
          >
            Neyla<span className="text-secondary-light">.tv</span>
          </Link>
        </div>
      </div>

      <div className="border-t border-neutral-800">
        <div className="mx-auto flex max-w-7xl flex-col items-center gap-4 px-6 py-6 sm:flex-row sm:justify-between">
          <div className="flex items-center gap-4 text-neutral-400">
            <Social label="X" href="https://x.com">
              <path d="M18 2h3l-7 8 8 12h-6l-5-7-5 7H2l8-10L2 2h6l4 6z" />
            </Social>
            <Social label="YouTube" href="https://youtube.com">
              <path d="M22 8.2a3 3 0 00-2.1-2.1C18 5.6 12 5.6 12 5.6s-6 0-7.9.5A3 3 0 002 8.2 31 31 0 002 12a31 31 0 00.1 3.8 3 3 0 002.1 2.1c1.9.5 7.8.5 7.8.5s6 0 7.9-.5a3 3 0 002.1-2.1A31 31 0 0022 12a31 31 0 00-.1-3.8zM10 15V9l5 3z" />
            </Social>
            <Social label="Instagram" href="https://instagram.com">
              <path d="M12 8a4 4 0 100 8 4 4 0 000-8zm0 1.8a2.2 2.2 0 110 4.4 2.2 2.2 0 010-4.4zM17 6.3a1 1 0 100 2 1 1 0 000-2zM12 4.2c2.5 0 2.8 0 3.8.06 2.5.12 3.7 1.3 3.8 3.8.05 1 .06 1.3.06 3.8s0 2.8-.06 3.8c-.12 2.5-1.3 3.7-3.8 3.8-1 .05-1.3.06-3.8.06s-2.8 0-3.8-.06c-2.5-.12-3.7-1.3-3.8-3.8C4.2 14.8 4.2 14.5 4.2 12s0-2.8.06-3.8C4.4 5.7 5.6 4.5 8 4.4c1-.05 1.3-.06 4-.06z" />
            </Social>
            <Social label="LinkedIn" href="https://linkedin.com">
              <path d="M6.9 8.8V19H3.6V8.8h3.3zM5.2 4a1.9 1.9 0 110 3.8 1.9 1.9 0 010-3.8zM20.4 19h-3.3v-5c0-1.2 0-2.7-1.7-2.7s-1.9 1.3-1.9 2.6V19H10.2V8.8h3.1v1.4h.05c.43-.8 1.5-1.7 3-1.7 3.2 0 3.8 2.1 3.8 4.9V19z" />
            </Social>
          </div>
          <p className="text-center text-xs text-neutral-500">
            © {year} Neyla TV. {t("footer.rights")}
          </p>
        </div>
      </div>
    </footer>
  );
}

function Social({
  label,
  href,
  children,
}: {
  label: string;
  href: string;
  children: React.ReactNode;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={label}
      className="text-neutral-400 transition hover:text-secondary-light"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
        {children}
      </svg>
    </a>
  );
}
