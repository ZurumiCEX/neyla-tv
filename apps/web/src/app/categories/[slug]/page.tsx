import { notFound } from "next/navigation";
import { LiveCard, type LiveChannel } from "@/components/LiveCard";
import { apiFetchServer } from "@/lib/api";
import { getServerT } from "@/lib/i18n-server";

type Resp = {
  category: { slug: string; name: string };
  results: LiveChannel[];
  total: number;
};

async function getCategory(slug: string): Promise<Resp | null> {
  try {
    return await apiFetchServer<Resp>(`/api/discover/categories/${slug}`);
  } catch (err) {
    const e = err as { status?: number };
    if (e.status === 404) return null;
    throw err;
  }
}

export default async function CategoryPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const [t, data] = await Promise.all([getServerT(), getCategory(slug)]);
  if (!data) notFound();

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <header>
        <p className="text-xs uppercase tracking-wider text-neutral-500">{t("cat.label")}</p>
        <h1 className="mt-1 text-2xl font-bold">{data.category.name}</h1>
        <p className="mt-1 text-sm text-neutral-400">
          {t("cat.liveCount", { total: data.total })}
        </p>
      </header>

      {data.results.length === 0 ? (
        <p className="mt-8 rounded-xl border border-dashed border-neutral-800 p-6 text-center text-sm text-neutral-500">
          {t("cat.empty")}
        </p>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {data.results.map((c) => (
            <LiveCard key={c.slug} channel={c} />
          ))}
        </div>
      )}
    </main>
  );
}
