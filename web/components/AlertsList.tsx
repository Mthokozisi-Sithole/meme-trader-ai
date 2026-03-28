"use client";

import type { Alert } from "@/types";

const SEVERITY_STYLES: Record<string, { bg: string; border: string; color: string; badge: string }> = {
  info: {
    bg: "rgba(68,136,255,0.06)",
    border: "rgba(68,136,255,0.25)",
    color: "var(--blue)",
    badge: "rgba(68,136,255,0.15)",
  },
  warning: {
    bg: "rgba(245,197,67,0.06)",
    border: "rgba(245,197,67,0.25)",
    color: "var(--yellow)",
    badge: "rgba(245,197,67,0.15)",
  },
  critical: {
    bg: "rgba(255,68,102,0.06)",
    border: "rgba(255,68,102,0.25)",
    color: "var(--red)",
    badge: "rgba(255,68,102,0.15)",
  },
};

interface Props {
  alerts: Alert[];
  onMarkRead?: (id: number) => void;
}

export function AlertsList({ alerts, onMarkRead }: Props) {
  if (alerts.length === 0) {
    return <p className="text-sm" style={{ color: "var(--text-dim)" }}>No alerts.</p>;
  }
  return (
    <ul className="space-y-1.5">
      {alerts.map((a) => {
        const s = SEVERITY_STYLES[a.severity] ?? SEVERITY_STYLES.info;
        return (
          <li
            key={a.id}
            className="border px-4 py-3 flex items-start justify-between gap-3 transition-opacity"
            style={{
              background: s.bg,
              borderColor: s.border,
              opacity: a.is_read ? 0.45 : 1,
            }}
          >
            <div className="min-w-0">
              <span className="font-bold text-sm mr-2" style={{ color: "var(--text-primary)" }}>
                {a.coin_symbol}
              </span>
              <span
                className="text-[10px] uppercase font-black px-1.5 py-0.5 mr-2"
                style={{ background: s.badge, color: s.color }}
              >
                {a.severity}
              </span>
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {a.message}
              </span>
            </div>
            {!a.is_read && onMarkRead && (
              <button
                onClick={() => onMarkRead(a.id)}
                className="text-xs shrink-0 px-2 py-1"
                style={{ color: "var(--text-dim)", border: "1px solid var(--border)" }}
              >
                Dismiss
              </button>
            )}
          </li>
        );
      })}
    </ul>
  );
}
