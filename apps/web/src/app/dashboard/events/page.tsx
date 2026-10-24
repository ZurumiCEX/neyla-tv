"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CalendarDays } from "lucide-react";
import { Panel } from "@/components/dashboard/kit";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

type PlatformEvent = {
  slug: string;
  title: string;
  kind: string;
  cover_url: string;
  link_url: string;
  starts_at: string;
  is_ongoing: boolean;
};

/** Événements de la plateforme auxquels les streamers peuvent participer. */
export default function DashboardEventsPage() {
  const t = useT();
  const { date, time } = useFormat();
  const [events, setEvents] = useState<PlatformEvent[] | null>(null);
  useEffect(() => {
    apiFetch<{ results: PlatformEvent[] }>("/api/events/upcoming?limit=20")
      .then((d) => setEvents(d.results))
      .catch(() => setEvents([]));
  }, []);
  return (
    <div className="mx-auto max-w-4xl">
      <Panel
        title={t("dash2.nav.events")}
        icon={CalendarDays}
        expandable={false}
        actions={
          <Link
            href="/calendrier"
            className="text-sm font-semibold text-emerald-300 hover:underline"
          >
            {t("dash2.fullCalendar")}
          </Link>
        }
        bodyClassName="p-0"
      >
        {events === null ? (
          <p className="p-4 text-sm text-neutral-500">{t("common.loading")}</p>
        ) : events.length === 0 ? (
          <p className="p-4 text-sm text-neutral-500">{t("dash2.noEvents")}</p>
        ) : (
          <ul className="divide-y divide-neutral-800/70">
            {events.map((e) => (
              <li key={e.slug}>
                <Link
                  href={e.link_url || `/calendrier#${e.slug}`}
                  className="flex items-center gap-4 px-4 py-3 hover:bg-neutral-800/50"
                >
                  <span className="w-16 shrink-0 text-center">
                    <span className="block text-xs uppercase text-neutral-500">
                      {date(e.starts_at, { month: "short" })}
                    </span>
                    <span className="block text-2xl font-bold">
                      {date(e.starts_at, { day: "numeric" })}
                    </span>
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-semibold">{e.title}</span>
                    <span className="text-xs text-neutral-500">
                      {t(`events.kind.${e.kind}`)} · {time(e.starts_at)}
                      {e.is_ongoing ? ` · ${t("dash2.ongoing")}` : ""}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
