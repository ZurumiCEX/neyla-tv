import { notFound } from "next/navigation";
import { LiveCard, type LiveChannel } from "@/components/LiveCard";
import { apiFetchServer } from "@/lib/api";

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
  const data = await getCategory(slug);
  if (!data) notFound();

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <header>
        <p className="text-xs uppercase tracking-wider text-neutral-500">
          Catégorie
        </p>
        <h1 className="mt-1 text-2xl font-bold">{data.category.name}</h1>
        <p className="mt-1 text-sm text-neutral-400">
          {data.total} live{data.total > 1 ? "s" : ""} en cours
        </p>
      </header>

      {data.results.length === 0 ? (
        <p className="mt-8 rounded-xl border border-dashed border-neutral-800 p-6 text-center text-sm text-neutral-500">
          Aucun live dans cette catégorie pour le moment.
        </p>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.results.map((c) => (
            <LiveCard key={c.slug} channel={c} />
          ))}
        </div>
      )}
    </main>
  );
}
