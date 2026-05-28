import { Suspense } from "react";
import { getServerT } from "@/lib/i18n-server";
import { SearchView } from "./SearchView";

export default async function SearchPage() {
  const t = await getServerT();
  return (
    <Suspense fallback={<main className="p-8 text-neutral-500">{t("common.loading")}</main>}>
      <SearchView />
    </Suspense>
  );
}
