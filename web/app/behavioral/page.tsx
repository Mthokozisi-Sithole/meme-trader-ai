"use client";

import { useState } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import type { BehavioralSignal, BehavioralSummary } from "@/types";

export const dynamic = "force-dynamic";

const SEVERITY_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  critical: { bg: "rgba(255,68,102,0.15)", color: "var(--red)", label: "CRITICAL" },
  alert: { bg: "rgba(255,152,0,0.15)", color: "#ff9800", label: "ALERT" },
  warning: { bg: "rgba(255,235,59,0.15)", color: "var(--yellow)", label: "WARNING" },
  info: { bg: "rgba(68,136,255,0.15)", color: "var(--blue)", label: "INFO" },
};

const PATTERN_BADGES: Record<string, { label: string; bg: string; color: string }> = {
  accumulation: { label: "ACCUM", bg: "rgba(0,217,126,0.15)", color: "#00d97e" },
  pre_breakout: { label: "PRE-BRK", bg: "rgba(68,136,255,0.15)", color: "#4488ff" },
  fake_breakout: { label: "FAKE", bg: "rgba(255,68,102,0.15)", color: "#ff4466" },
  liquidity_trap: { label: "LIQ TRAP", bg: "rgba(255,152,0,0.15)", color: "#ff9800" },
  momentum_ignition: { label: "MOM IGN", bg: "rgba(168,85,247,0.15)", color: "var(--purple)" },
  volume_anomaly: { label: "VOL ANOM", bg: "rgba(255,235,59,0.15)", color: "var(--yellow)" },
  wash_trading: { label: "WASH", bg: "rgba(255,68,102,0.12)", color: "#ff6680" },
  rug_risk: { label: "RUG", bg: "rgba(255,68,102,0.2)", color: "#ff1133" },
  smart_money_entry: { label: "SMART $", bg: "rgba(0,217,126,0.15)", color: "#00ff99" },
  dev_exit: { label: "DEV EXIT", bg: "rgba(255,152,0,0.15)", color: "#ffb340" },
};

function fmtTime(iso: string): string {
  const d = new Date(iso);
  const now = Date.now();
  const diff = now - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function SeverityBadge({ severity }: { severity: BehavioralSignal["severity"] }) {
  const style = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.info;
  return (
    <span
      className="text-[11px] font-bold px-1.5 py-0.5"
      style={{ background: style.bg, color: style.color, border: `1px solid ${style.color}44` }}
    >
      {style.label}
    </span>
  );
}

function PatternBadge({ pattern }: { pattern: string }) {
  const style = PATTERN_BADGES[pattern];
  if (!style) {
    return (
      <span
        className="text-[11px] font-semibold px-1.5 py-0.5"
        style={{ background: "var(--bg-card)", color: "var(--text-secondary)", border: "1px solid var(--border)" }}
      >
        {pattern.toUpperCase().slice(0, 10)}
      </span>
    );
  }
  return (
    <span
      className="text-[11px] font-bold px-1.5 py-0.5"
      style={{ background: style.bg, color: style.color, border: `1px solid ${style.color}44` }}
    >
      {style.label}
    </span>
  );
}

function StatCard({ label, value, valueColor }: { label: string; value: string | number; valueColor?: string }) {
  return (
    <div
      className="p-4 border"
      style={{ background: "var(--bg-card)", borderColor: "var(--border)" }}
    >
      <div className="text-[11px] uppercase tracking-wider mb-1" style={{ color: "var(--text-dim)" }}>
        {label}
      </div>
      <div className="text-2xl font-black mono" style={{ color: valueColor ?? "var(--text-primary)" }}>
        {value}
      </div>
    </div>
  );
}

export default function BehavioralPage() {
  const [severity, setSeverity] = useState("");
  const [patternType, setPatternType] = useState("");

  const { data: signals, isLoading, error } = useSWR<BehavioralSignal[]>(
    ["/behavioral/signals", severity, patternType],
    () =>
      api.behavioral.signals({
        severity: severity || undefined,
        pattern_type: patternType || undefined,
        limit: 200,
      }),
    { refreshInterval: 15_000 }
  );

  const { data: summary } = useSWR<BehavioralSummary>(
    "/behavioral/summary",
    () => api.behavioral.summary(),
    { refreshInterval: 15_000 }
  );

  const activeSignals = signals?.filter((s) => s.is_active) ?? [];
  const criticalCount = summary?.by_severity?.critical ?? 0;
  const warningCount = summary?.by_severity?.warning ?? 0;
  const patternCount = summary ? Object.keys(summary.by_pattern).length : 0;

  const allPatternTypes = signals
    ? Array.from(new Set(signals.map((s) => s.pattern_type))).sort()
    : [];

  return (
    <div className="space-y-4 pt-4">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-black uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
            Behavioral Signals
          </h1>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-dim)" }}>
            Live pattern detection — {summary?.total_active ?? activeSignals.length} active signals
          </p>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total Active" value={summary?.total_active ?? activeSignals.length} />
        <StatCard label="Critical" value={criticalCount} valueColor={criticalCount > 0 ? "var(--red)" : undefined} />
        <StatCard label="Warnings" value={warningCount} valueColor={warningCount > 0 ? "var(--yellow)" : undefined} />
        <StatCard label="Patterns Detected" value={patternCount} valueColor="var(--blue)" />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          className="text-sm px-3 py-2 focus:outline-none"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            color: "var(--text-secondary)",
          }}
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="alert">Alert</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>
        <select
          value={patternType}
          onChange={(e) => setPatternType(e.target.value)}
          className="text-sm px-3 py-2 focus:outline-none"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            color: "var(--text-secondary)",
          }}
        >
          <option value="">All Patterns</option>
          {allPatternTypes.map((pt) => (
            <option key={pt} value={pt}>
              {PATTERN_BADGES[pt]?.label ?? pt}
            </option>
          ))}
        </select>
      </div>

      {isLoading && (
        <div className="text-center py-16 text-sm" style={{ color: "var(--text-dim)" }}>
          Loading signals…
        </div>
      )}
      {error && (
        <div className="p-4 text-sm border" style={{ background: "rgba(255,68,102,0.08)", borderColor: "rgba(255,68,102,0.3)", color: "var(--red)" }}>
          Failed to load. Is the API running?
        </div>
      )}
      {signals && signals.length === 0 && (
        <div className="text-center py-16 text-sm" style={{ color: "var(--text-dim)" }}>
          No behavioral signals detected yet.
        </div>
      )}

      {signals && signals.length > 0 && (
        <div className="overflow-x-auto border" style={{ borderColor: "var(--border)" }}>
          <table className="min-w-full divide-y text-sm" style={{ borderColor: "var(--border)" }}>
            <thead style={{ background: "var(--bg-card)" }}>
              <tr>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: "var(--text-dim)" }}>Token</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: "var(--text-dim)" }}>Pattern</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden md:table-cell" style={{ color: "var(--text-dim)" }}>Label</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: "var(--text-dim)" }}>Confidence</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: "var(--text-dim)" }}>Severity</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden lg:table-cell" style={{ color: "var(--text-dim)" }}>Fusion Score</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden sm:table-cell" style={{ color: "var(--text-dim)" }}>Chain</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden md:table-cell" style={{ color: "var(--text-dim)" }}>Time</th>
              </tr>
            </thead>
            <tbody style={{ background: "var(--bg-base)" }}>
              {[...signals]
                .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                .map((s) => (
                  <tr
                    key={s.id}
                    className="transition-colors"
                    style={{ borderBottom: "1px solid var(--border)" }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-card)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    <td className="px-3 py-2">
                      <div className="font-bold" style={{ color: "var(--text-primary)" }}>
                        {s.token_symbol ?? s.token_address.slice(0, 8) + "…"}
                      </div>
                      <div className="text-[11px] mono" style={{ color: "var(--text-dim)" }}>
                        {s.token_address.slice(0, 8)}…
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      <PatternBadge pattern={s.pattern_type} />
                    </td>
                    <td className="px-3 py-2 hidden md:table-cell">
                      <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                        {s.signal_label}
                      </span>
                    </td>
                    <td className="px-3 py-2 mono">
                      <span
                        className="text-xs font-semibold"
                        style={{
                          color:
                            s.confidence >= 0.8
                              ? "var(--green)"
                              : s.confidence >= 0.5
                              ? "var(--yellow)"
                              : "var(--text-secondary)",
                        }}
                      >
                        {(s.confidence * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <SeverityBadge severity={s.severity} />
                    </td>
                    <td className="px-3 py-2 mono hidden lg:table-cell">
                      <span
                        className="text-xs font-semibold"
                        style={{
                          color:
                            s.fusion_score >= 80
                              ? "var(--green)"
                              : s.fusion_score >= 60
                              ? "var(--yellow)"
                              : "var(--text-secondary)",
                        }}
                      >
                        {s.fusion_score.toFixed(1)}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-xs hidden sm:table-cell" style={{ color: "var(--text-secondary)" }}>
                      {s.chain.toUpperCase()}
                    </td>
                    <td className="px-3 py-2 text-xs hidden md:table-cell" style={{ color: "var(--text-dim)" }}>
                      {fmtTime(s.created_at)}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
