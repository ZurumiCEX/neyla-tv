import type { Metadata } from "next";
import { LegalDocument } from "@/components/LegalDocument";

export const metadata: Metadata = { title: "Règles de la communauté — Neyla TV" };

export default function Page() {
  return <LegalDocument slug="guidelines" />;
}
