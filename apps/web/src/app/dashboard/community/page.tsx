"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Ban, Handshake, Star, Users } from "lucide-react";
import { Avatar } from "@/components/Avatar";
import { ChatBansManager } from "@/components/ChatBansManager";
import { CollaborationManager } from "@/components/CollaborationManager";
import { Panel, SettingRow, Switch, useDashboard } from "@/components/dashboard/kit";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

type Member = {
  username: string;
  display_name: string;
  avatar_url: string;
  since: string;
  until?: string;
  gifted_by?: string | null;
};

function MemberList({ path, empty }: { path: string; empty: string }) {
  const t = useT();
  const { date } = useFormat();
  const { authFetch } = useAuth();
  const [data, setData] = useState<{ count: number; results: Member[] } | null>(null);
  useEffect(() => {
    authFetch<{ count: number; results: Member[] }>(path)
      .then(setData)
      .catch(() => setData({ count: 0, results: [] }));
  }, [authFetch, path]);
  if (!data) return <p className="p-4 text-sm text-neutral-500">{t("common.loading")}</p>;
  if (data.results.length === 0) return <p className="p-4 text-sm text-neutral-500">{empty}</p>;
  return (
    <ul className="divide-y divide-neutral-800/70">
      {data.results.map((m) => (
        <li key={m.username}>
          <Link
            href={`/u/${m.username}`}
            className="flex items-center gap-3 px-4 py-2.5 hover:bg-neutral-800/50"
          >
            <Avatar src={m.avatar_url} name={m.display_name} size={32} />
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-semibold">{m.display_name}</span>
              <span className="block text-xs text-neutral-500">
                {t("dash2.since", {
                  date: date(m.since, { day: "numeric", month: "short", year: "numeric" }),
                })}
                {m.gifted_by ? ` · ${t("dash2.giftedBy", { user: m.gifted_by })}` : ""}
              </span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

export default function DashboardCommunityPage() {
  const t = useT();
  const { authFetch } = useAuth();
  const { channel, setChannel } = useDashboard();
  if (!channel) return <p className="text-neutral-500">{t("common.loading")}</p>;

  async function toggleCollab(next: boolean) {
    setChannel({ ...channel!, collaborations_open: next });
    try {
      setChannel(
        await authFetch("/api/channels/me", {
          method: "PATCH",
          body: JSON.stringify({ collaborations_open: next }),
        }),
      );
    } catch {
      setChannel({ ...channel!, collaborations_open: !next });
    }
  }

  return (
    <div className="mx-auto grid max-w-6xl gap-4 lg:grid-cols-2">
      <Panel title={t("dash2.followers")} icon={Users} className="h-96" bodyClassName="p-0">
        <MemberList path="/api/channels/me/followers" empty={t("dash2.noFollowers")} />
      </Panel>
      <Panel title={t("dash2.subscribers")} icon={Star} className="h-96" bodyClassName="p-0">
        <MemberList path="/api/channels/me/subscribers" empty={t("dash2.noSubscribers")} />
      </Panel>
      <Panel title={t("dash2.bans")} icon={Ban}>
        <ChatBansManager />
      </Panel>
      <Panel title={t("dash.tab.collaboration")} icon={Handshake}>
        <SettingRow label={t("collab.openTitle")} hint={t("collab.openDesc")}>
          <Switch
            label={t("collab.openTitle")}
            checked={channel.collaborations_open}
            onChange={toggleCollab}
          />
        </SettingRow>
        <div className="mt-3">
          <CollaborationManager />
        </div>
      </Panel>
    </div>
  );
}
