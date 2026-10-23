import type { Metadata } from "next";
import { LegalDocument } from "@/components/LegalDocument";

export const metadata: Metadata = { title: "Contact — Neyla TV" };

export default function Page() {
  return <LegalDocument slug="contact" />;
}
