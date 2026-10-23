import Link from "next/link";
import { getServerT } from "@/lib/i18n-server";

export default async function NotFound() {
  const t = await getServerT();
  return (
    <main className="mx-auto flex max-w-md flex-col items-center justify-center px-4 py-20 text-center">
      <h1 className="text-2xl font-bold">{t("channel.notFound")}</h1>
      <p className="mt-2 text-neutral-400">{t("channel.notFoundDesc")}</p>
      <Link href="/" className="mt-6 text-emerald-300 underline">
        {t("common.backHome")}
      </Link>
    </main>
  );
}
