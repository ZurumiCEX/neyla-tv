import type { Metadata } from "next";
import { LegalDocument } from "@/components/LegalDocument";

export const metadata: Metadata = { title: "Droits d'auteur — Neyla TV" };

export default function Page() {
  return <LegalDocument slug="dmca" />;
}
