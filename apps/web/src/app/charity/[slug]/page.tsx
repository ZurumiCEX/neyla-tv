import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { apiFetchServer } from "@/lib/api";
import { getServerT } from "@/lib/i18n-server";

type Detail = {
  event: {
    slug: string;
    title: string;
    theme: string;
    description_md: string;
    cover_url: string;
    starts_at: string;
    ends_at: string;
    is_open: boolean;
  };
  total: number;
  donor_count: number;
  by_charity: { charity__slug: string; charity__name: string; total: number; count: number }[];
  top_donors: { display_name: string; aura_amount: number }[];
  disbursed_aura: number;
  disbursed_xof: number;
  pending_aura: number;
  disbursements: {
    charity: string;
    fiat_amount_xof: number;
    reference: string;
    paid_at: string;
    proof_url: string;
  }[];
};

async function getDetail(slug: string): Promise<Detail | null> {
  try {
    return await apiFetchServer<Detail>(`/api/charity/events/${encodeURIComponent(slug)}`);
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const d = await getDetail((await params).slug);
  return { title: d ? `${d.event.title} — Charity Day` : "Charity Day — Neyla TV" };
}

/** Bilan public d'un Charity Day : dons, répartition, versements effectués. */
export default async function CharityEventPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const [t, d] = await Promise.all([getServerT(), getDetail(slug)]);
  if (!d) notFound();
  const n = (v: number) => v.toLocaleString("fr-FR");
  const date = (iso: string) =>
    new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
  return (
    <main className="mx-auto max-w-4xl space-y-5 p-4 sm:p-8">
      <Link href="/charity/archives" className="text-sm text-neutral-400 hover:text-emerald-300">
        ← {t("charity.archives.title")}
      </Link>
      <header className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/60">
        {d.event.cover_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={d.event.cover_url} alt="" className="aspect-[3/1] w-full object-cover" />
        )}
        <div className="p-5">
          <p className="text-xs text-neutral-500">
            {date(d.event.starts_at)} → {date(d.event.ends_at)}
          </p>
          <h1 className="mt-1 text-2xl font-bold">{d.event.title}</h1>
          {d.event.theme && <p className="text-neutral-400">{d.event.theme}</p>}
          {d.event.is_open && (
            <Link
              href="/charity"
              className="mt-3 inline-block rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-neutral-950"
            >
              {t("charity.archives.donateNow")}
            </Link>
          )}
        </div>
      </header>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          [t("charity.archives.raised"), `${n(d.total)} Aura`],
          [t("charity.archives.donors"), n(d.donor_count)],
          [t("charity.archives.paid"), `${n(d.disbursed_xof)} FCFA`],
          [t("charity.archives.pending"), `${n(d.pending_aura)} Aura`],
        ].map(([label, value]) => (
          <div key={label} className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
            <p className="text-xs uppercase tracking-wider text-neutral-500">{label}</p>
            <p className="mt-1 text-xl font-bold tabular-nums">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
          <h2 className="mb-3 font-bold">{t("charity.archives.byCharity")}</h2>
          <ul className="space-y-2 text-sm">
            {d.by_charity.map((c) => (
              <li key={c.charity__slug} className="flex justify-between gap-3">
                <span>{c.charity__name}</span>
                <span className="font-semibold tabular-nums">{n(c.total)} Aura</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
          <h2 className="mb-3 font-bold">{t("charity.archives.topDonors")}</h2>
          <ol className="space-y-2 text-sm">
            {d.top_donors.map((x, i) => (
              <li key={i} className="flex justify-between gap-3">
                <span>
                  {i + 1}. {x.display_name}
                </span>
                <span className="font-semibold tabular-nums">{n(x.aura_amount)} Aura</span>
              </li>
            ))}
          </ol>
        </section>
      </div>

      <section className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
        <h2 className="mb-3 font-bold">{t("charity.archives.disbursements")}</h2>
        {d.disbursements.length === 0 ? (
          <p className="text-sm text-neutral-500">{t("charity.archives.noDisbursement")}</p>
        ) : (
          <ul className="divide-y divide-neutral-800 text-sm">
            {d.disbursements.map((x) => (
              <li key={x.reference} className="flex flex-wrap justify-between gap-2 py-2">
                <span>
                  {x.charity} · <span className="text-neutral-500">{x.reference}</span>
                </span>
                <span className="font-semibold tabular-nums">
                  {n(x.fiat_amount_xof)} FCFA · {date(x.paid_at)}
                  {x.proof_url && (
                    <a
                      href={x.proof_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-2 text-emerald-300 underline"
                    >
                      {t("charity.archives.proof")}
                    </a>
                  )}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
