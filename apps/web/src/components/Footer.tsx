"use client";

// Pied de page (inspiré de Kick) : Entreprise · Ressources · Légal · Contact,
// puis réseaux sociaux et mentions. Adresses de contact et liens sociaux
// configurables via NEXT_PUBLIC_CONTACT_* / NEXT_PUBLIC_SOCIAL_* (un réseau sans
// URL configurée n'est pas affiché).

import Link from "next/link";
import { useT } from "@/lib/i18n";

type FooterLink = { label: string; href: string };

const CONTACT = {
  support: process.env.NEXT_PUBLIC_CONTACT_SUPPORT || "support@neyla.tv",
  partners: process.env.NEXT_PUBLIC_CONTACT_PARTNERS || "partners@neyla.tv",
  press: process.env.NEXT_PUBLIC_CONTACT_PRESS || "press@neyla.tv",
};

const SOCIALS: { key: string; label: string; href?: string; path: string }[] = [
  {
    key: "x",
    label: "X",
    href: process.env.NEXT_PUBLIC_SOCIAL_X,
    path: "M18 2h3l-7 8 8 12h-6l-5-7-5 7H2l8-10L2 2h6l4 6z",
  },
  {
    key: "instagram",
    label: "Instagram",
    href: process.env.NEXT_PUBLIC_SOCIAL_INSTAGRAM,
    path: "M12 8a4 4 0 100 8 4 4 0 000-8zm0 1.8a2.2 2.2 0 110 4.4 2.2 2.2 0 010-4.4zM17 6.3a1 1 0 100 2 1 1 0 000-2zM12 4.2c2.5 0 2.8 0 3.8.06 2.5.12 3.7 1.3 3.8 3.8.05 1 .06 1.3.06 3.8s0 2.8-.06 3.8c-.12 2.5-1.3 3.7-3.8 3.8-1 .05-1.3.06-3.8.06s-2.8 0-3.8-.06c-2.5-.12-3.7-1.3-3.8-3.8C4.2 14.8 4.2 14.5 4.2 12s0-2.8.06-3.8C4.4 5.7 5.6 4.5 8 4.4c1-.05 1.3-.06 4-.06z",
  },
  {
    key: "tiktok",
    label: "TikTok",
    href: process.env.NEXT_PUBLIC_SOCIAL_TIKTOK,
    path: "M16.5 3c.4 2.3 1.8 3.8 4 4v3.1a7.3 7.3 0 01-4-1.2v6.3A5.8 5.8 0 1110.7 9.4v3.2a2.7 2.7 0 102 2.6V3z",
  },
  {
    key: "discord",
    label: "Discord",
    href: process.env.NEXT_PUBLIC_SOCIAL_DISCORD,
    path: "M19.6 5.6A16 16 0 0015.7 4.4l-.5 1a14.8 14.8 0 00-6.4 0l-.5-1A16 16 0 004.4 5.6 16.6 16.6 0 001.5 17a16.2 16.2 0 004.9 2.5l1-1.6a10.4 10.4 0 01-1.6-.8l.4-.3a11.5 11.5 0 009.6 0l.4.3-1.6.8 1 1.6a16.1 16.1 0 004.9-2.5 16.5 16.5 0 00-2.9-11.4zM8.7 14.6c-.9 0-1.7-.9-1.7-2s.7-2 1.7-2 1.7.9 1.7 2-.8 2-1.7 2zm6.6 0c-.9 0-1.7-.9-1.7-2s.7-2 1.7-2 1.7.9 1.7 2-.7 2-1.7 2z",
  },
  {
    key: "youtube",
    label: "YouTube",
    href: process.env.NEXT_PUBLIC_SOCIAL_YOUTUBE,
    path: "M22 8.2a3 3 0 00-2.1-2.1C18 5.6 12 5.6 12 5.6s-6 0-7.9.5A3 3 0 002 8.2 31 31 0 002 12a31 31 0 00.1 3.8 3 3 0 002.1 2.1c1.9.5 7.8.5 7.8.5s6 0 7.9-.5a3 3 0 002.1-2.1A31 31 0 0022 12a31 31 0 00-.1-3.8zM10 15V9l5 3z",
  },
];

export function Footer() {
  const t = useT();
  const year = new Date().getFullYear();

  const columns: { title: string; links: FooterLink[] }[] = [
    {
      title: t("footer.company"),
      links: [
        { label: t("footer.about"), href: "/about" },
        { label: t("nav.becomeStreamer"), href: "/become-streamer" },
        { label: t("footer.charity"), href: "/charity" },
        { label: t("footer.status"), href: "/statut" },
      ],
    },
    {
      title: t("footer.resources"),
      links: [
        { label: t("footer.help"), href: "/guides" },
        { label: t("nav.events"), href: "/calendrier" },
        { label: t("side.shorts"), href: "/instant" },
        { label: t("footer.referral"), href: "/invite" },
      ],
    },
    {
      title: t("footer.legal"),
      links: [
        { label: t("footer.guidelines"), href: "/guidelines" },
        { label: t("footer.copyright"), href: "/dmca" },
        { label: t("footer.privacy"), href: "/privacy" },
        { label: t("footer.terms"), href: "/terms" },
        { label: t("footer.cookies"), href: "/cookies" },
        { label: t("footer.auraTerms"), href: "/terms#aura" },
        { label: t("footer.partnerTerms"), href: "/terms#partenaires" },
      ],
    },
  ];

  const contacts = [
    { label: t("footer.contactSupport"), email: CONTACT.support },
    { label: t("footer.contactPartners"), email: CONTACT.partners },
    { label: t("footer.contactPress"), email: CONTACT.press },
  ];
  const socials = SOCIALS.filter((s) => Boolean(s.href));

  return (
    <footer className="mt-12 border-t border-neutral-800 bg-neutral-950">
      <div className="px-6 py-10">
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {columns.map((c) => (
            <nav key={c.title} aria-label={c.title}>
              <p className="mb-3 text-sm font-bold text-neutral-100">{c.title}</p>
              <ul className="space-y-2">
                {c.links.map((l) => (
                  <li key={l.href}>
                    <Link
                      href={l.href}
                      className="text-sm text-neutral-400 transition hover:text-secondary-light"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}

          <div>
            <p className="mb-3 text-sm font-bold text-neutral-100">{t("footer.contact")}</p>
            <ul className="space-y-2">
              {contacts.map((c) => (
                <li key={c.email} className="text-sm text-neutral-400">
                  {c.label} :{" "}
                  <a href={`mailto:${c.email}`} className="transition hover:text-secondary-light">
                    {c.email}
                  </a>
                </li>
              ))}
              <li>
                <Link
                  href="/contact"
                  className="text-sm text-neutral-400 transition hover:text-secondary-light"
                >
                  {t("footer.feedback")}
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {socials.length > 0 && (
          <div className="mt-10 flex flex-wrap gap-2">
            {socials.map((s) => (
              <a
                key={s.key}
                href={s.href}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={s.label}
                title={s.label}
                className="flex h-10 w-10 items-center justify-center rounded-lg bg-neutral-900 text-neutral-300 transition hover:bg-neutral-800 hover:text-secondary-light"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                  <path d={s.path} />
                </svg>
              </a>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-neutral-800">
        <div className="flex flex-col items-center gap-2 px-6 py-5 sm:flex-row sm:justify-between">
          <Link href="/" className="text-lg font-extrabold tracking-tight">
            Neyla<span className="text-secondary-light">.tv</span>
          </Link>
          <p className="text-center text-xs text-neutral-500">
            © {year} Neyla TV. {t("footer.rights")}
          </p>
        </div>
      </div>
    </footer>
  );
}
