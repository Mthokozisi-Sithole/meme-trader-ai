"use client";

import useSWR, { mutate } from "swr";
import { api } from "@/lib/api";
import { AlertsList } from "@/components/AlertsList";
import type { Alert } from "@/types";

export const dynamic = "force-dynamic";

export default function AlertsPage() {
  const { data: alerts, isLoading } = useSWR<Alert[]>(
    "/alerts/",
    () => api.alerts.list(),
    { refreshInterval: 15_000 }
  );

  async function handleMarkRead(id: number) {
    await api.alerts.markRead(id);
    await mutate("/alerts/");
  }

  async function handleMarkAllRead() {
    const unread = alerts?.filter((a) => !a.is_read) ?? [];
    await Promise.all(unread.map((a) => api.alerts.markRead(a.id)));
    await mutate("/alerts/");
  }

  const unread = alerts?.filter((a) => !a.is_read).length ?? 0;

  return (
    <div className="space-y-4 pt-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-black uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
            Risk Alerts
          </h1>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-dim)" }}>
            {unread} unread
          </p>
        </div>
        <div className="flex gap-2">
          {unread > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="text-xs px-3 py-2 transition-colors"
              style={{ border: "1px solid var(--border)", color: "var(--text-secondary)" }}
            >
              Mark all read
            </button>
          )}
          <button
            onClick={() => mutate("/alerts/")}
            className="text-xs px-3 py-2 transition-colors"
            style={{ border: "1px solid var(--border)", color: "var(--text-secondary)" }}
          >
            Refresh
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="text-sm" style={{ color: "var(--text-dim)" }}>Loading…</div>
      )}
      {alerts && alerts.length === 0 && (
        <div className="text-center py-16 text-sm" style={{ color: "var(--text-dim)" }}>
          No alerts.
        </div>
      )}
      {alerts && alerts.length > 0 && (
        <AlertsList alerts={alerts} onMarkRead={handleMarkRead} />
      )}
    </div>
  );
}
