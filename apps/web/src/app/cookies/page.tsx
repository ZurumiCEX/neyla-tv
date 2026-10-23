import type { Metadata } from "next";
import { LegalDocument } from "@/components/LegalDocument";

export const metadata: Metadata = { title: "Politique cookies — Neyla TV" };

export default function Page() {
  return <LegalDocument slug="cookies" />;
}
