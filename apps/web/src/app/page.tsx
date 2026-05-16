// Page d'accueil Phase 0 : appelle /api/healthz côté serveur et affiche l'état.
type HealthPayload = {
  status: "ok" | "degraded";
  db: boolean;
  redis: boolean;
};

async function fetchHealth(): Promise<HealthPayload | null> {
  const base = process.env.API_URL_INTERNAL ?? "http://api:8000";
  try {
    const res = await fetch(`${base}/api/healthz`, { cache: "no-store" });
    return (await res.json()) as HealthPayload;
  } catch {
    return null;
  }
}

function Pill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm ${
        ok ? "bg-emerald-500/15 text-emerald-300" : "bg-red-500/15 text-red-300"
      }`}
    >
      <span className={`h-2 w-2 rounded-full ${ok ? "bg-emerald-400" : "bg-red-400"}`} />
      {label}
    </span>
  );
}

export default async function HomePage() {
  const health = await fetchHealth();

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold">Neyla TV</h1>
      <p className="text-neutral-400">
        MVP de plateforme de streaming jeux vidéo. Phase 0 : bootstrap.
      </p>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
        <h2 className="mb-4 text-xl font-semibold">État des services</h2>
        {health ? (
          <div className="flex flex-wrap gap-3">
            <Pill ok={health.status === "ok"} label={`API : ${health.status}`} />
            <Pill ok={health.db} label="Postgres" />
            <Pill ok={health.redis} label="Redis" />
          </div>
        ) : (
          <p className="text-red-300">API injoignable.</p>
        )}
      </section>
    </main>
  );
}
