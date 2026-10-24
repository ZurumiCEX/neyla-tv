"use client";

import RevenusPage from "@/app/revenus/page";
import { SubTierSettings } from "@/components/dashboard/SubTierSettings";

export default function DashboardRevenuePage() {
  return (
    <div className="space-y-4">
      {/* Le contenu de /revenus a sa propre mise en page centrée. */}
      <div className="[&>main]:max-w-none [&>main]:p-0">
        <RevenusPage />
      </div>
      <div className="mx-auto max-w-5xl">
        <SubTierSettings />
      </div>
    </div>
  );
}
