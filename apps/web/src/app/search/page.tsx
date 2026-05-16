import { Suspense } from "react";
import { SearchView } from "./SearchView";

export default function SearchPage() {
  return (
    <Suspense fallback={<main className="p-8 text-neutral-500">Chargement…</main>}>
      <SearchView />
    </Suspense>
  );
}
