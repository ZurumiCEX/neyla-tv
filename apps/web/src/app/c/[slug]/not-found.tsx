import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex max-w-md flex-col items-center justify-center px-4 py-20 text-center">
      <h1 className="text-2xl font-bold">Chaîne introuvable</h1>
      <p className="mt-2 text-neutral-400">Personne ne diffuse sous ce slug.</p>
      <Link href="/" className="mt-6 text-emerald-300 underline">
        Retour à l&apos;accueil
      </Link>
    </main>
  );
}
