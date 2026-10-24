"use client";

import { MessageSquare, MonitorPlay } from "lucide-react";
import { ChatPanel } from "@/components/ChatPanel";
import { HlsPlayer } from "@/components/HlsPlayer";
import { Panel, useDashboard } from "@/components/dashboard/kit";
import {
  ActivityFeedPanel,
  ChannelActionsPanel,
  ModActionsPanel,
  SessionInfoPanel,
  StreamInfoPanel,
} from "@/components/dashboard/widgets";
import { useT } from "@/lib/i18n";

/** Page « Stream » : widgets du direct, à la manière du tableau de bord Kick. */
export default function DashboardStreamPage() {
  const t = useT();
  const { channel } = useDashboard();

  if (!channel) {
    return (
      <div className="grid animate-pulse gap-3 lg:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-64 rounded-lg border border-neutral-800 bg-neutral-900" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-3 xl:grid-cols-[minmax(0,1.55fr)_minmax(300px,1fr)_minmax(280px,0.85fr)]">
      <div className="flex min-w-0 flex-col gap-3">
        <SessionInfoPanel />
        <Panel title={t("dash2.streamPreview")} icon={MonitorPlay} bodyClassName="p-0">
          <HlsPlayer
            src={channel.playback_url}
            poster={channel.thumbnail_url}
            isLive={channel.is_live}
            className="!rounded-none !border-0"
          />
        </Panel>
        <div className="grid gap-3 md:grid-cols-2">
          <ActivityFeedPanel className="h-80" />
          <ModActionsPanel className="h-80" />
        </div>
      </div>

      <Panel
        title={t("chat.title")}
        icon={MessageSquare}
        className="h-[70vh] xl:h-[calc(100vh-130px)] xl:sticky xl:top-3"
        bodyClassName="p-0"
      >
        <div className="h-full [&>section]:h-full [&>section]:rounded-none [&>section]:border-0">
          <ChatPanel slug={channel.slug} isLive={channel.is_live} hideHeader />
        </div>
      </Panel>

      <div className="flex min-w-0 flex-col gap-3">
        <StreamInfoPanel />
        <ChannelActionsPanel />
      </div>
    </div>
  );
}
