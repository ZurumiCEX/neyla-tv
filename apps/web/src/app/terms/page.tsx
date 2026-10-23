import type { Metadata } from "next";
import { LegalDocument } from "@/components/LegalDocument";

export const metadata: Metadata = { title: "Conditions générales d'utilisation — Neyla TV" };

export default function Page() {
  return <LegalDocument slug="terms" />;
}
