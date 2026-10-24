import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CalendarDays, ExternalLink } from "lucide-react";
import { apiFetchServer } from "@/lib/api";
import { getServerT } from "@/lib/i18n-server";

type PlatformEvent = {
  slug: string;
  title: string;
  kind: string;
  description_md: string;
  cover_url: string;
  link_url: string;
  starts_at: string;
  ends_at: string;
  is_ongoing: boolean;
};

async function getEvent(slug: string): Promise<PlatformEvent | null> {
  try {
    return await apiFetchServer<PlatformEvent>(`/api/events/${encodeURIComponent(slug)}`);
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const ev = await getEvent(slug);
  return { title: ev ? `${ev.title} — Neyla TV` : "Événement — Neyla TV" };
}

/** Détail d'un événement de la plateforme (tournoi, première, Charity Day…). */
export default async function EventPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const [t, ev] = await Promise.all([getServerT(), getEvent(slug)]);
  if (!ev) notFound();
  const fmt = (iso: string) =>
    new Date(iso).toLocaleString("fr-FR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Africa/Dakar",
    });
  const internal = ev.link_url.startsWith("/");
  return (
    <main className="mx-auto max-w-3xl p-4 sm:p-8">
      <Link href="/calendrier" className="text-sm text-neutral-400 hover:text-emerald-300">
        ← {t("events.backToCalendar")}
      </Link>
      <article className="mt-3 overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/60">
        {ev.cover_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={ev.cover_url} alt="" className="aspect-[3/1] w-full object-cover" />
        )}
        <div className="space-y-4 p-5 sm:p-6">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-neutral-800 px-2.5 py-0.5 text-xs font-semibold text-neutral-300">
              {t(`events.kind.${ev.kind}`)}
            </span>
            {ev.is_ongoing && (
              <span className="rounded-full bg-red-600 px-2.5 py-0.5 text-xs font-bold text-white">
                {t("events.ongoing")}
              </span>
            )}
          </div>
          <h1 className="text-2xl font-bold sm:text-3xl">{ev.title}</h1>
          <p className="flex items-start gap-2 text-sm text-neutral-300">
            <CalendarDays size={16} className="mt-0.5 shrink-0 text-emerald-400" aria-hidden />
            <span>
              {fmt(ev.starts_at)} → {fmt(ev.ends_at)}
              <span className="block text-xs text-neutral-500">{t("events.timezone")}</span>
            </span>
          </p>
          {ev.description_md && (
            <div className="space-y-3 text-[15px] leading-relaxed text-neutral-200">
              {ev.description_md.split(/\n{2,}/).map((para, i) => (
                <p key={i} className="whitespace-pre-line">
                  {para}
                </p>
              ))}
            </div>
          )}
          {ev.link_url && (
            <a
              href={ev.link_url}
              {...(internal ? {} : { target: "_blank", rel: "noopener noreferrer" })}
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-neutral-950 hover:bg-emerald-400"
            >
              {t("events.open")} {!internal && <ExternalLink size={14} aria-hidden />}
            </a>
          )}
        </div>
      </article>
    </main>
  );
}
