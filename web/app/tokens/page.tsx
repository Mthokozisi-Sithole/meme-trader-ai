"use client";

import { useState } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import type { DexToken } from "@/types";

export const dynamic = "force-dynamic";

function fmtPrice(n: number | null | undefined): string {
  if (n == null) return "—";
  if (n < 0.000001) return `$${n.toExponential(3)}`;
  if (n < 0.001) return `$${n.toFixed(7)}`;
  if (n < 1) return `$${n.toFixed(5)}`;
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 4 })}`;
}

function fmtCompact(n: number | null | undefined): string {
  if (n == null) return "—";
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

function fmtAge(hours: number | null | undefined): string {
  if (hours == null) return "—";
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 24) return `${hours.toFixed(1)}h`;
  return `${(hours / 24).toFixed(1)}d`;
}

function PctCell({ v }: { v: number | null }) {
  if (v == null) return <span style={{ color: "var(--text-dim)" }}>—</span>;
  return (
    <span className="mono font-semibold" style={{ color: v >= 0 ? "var(--green)" : "var(--red)" }}>
      {v >= 0 ? "+" : ""}{v.toFixed(1)}%
    </span>
  );
}

const BAND_DOT: Record<string, string> = {
  "Strong Buy": "bg-green-500",
  Watch: "bg-yellow-500",
  Risky: "bg-orange-500",
  Avoid: "bg-red-500",
};

const CHAIN_LABELS: Record<string, string> = {
  solana: "SOL",
  ethereum: "ETH",
  bsc: "BSC",
  base: "BASE",
};

const NARRATIVE_BADGE: Record<string, string> = {
  AI: "bg-blue-900/50 text-blue-300",
  Political: "bg-red-900/50 text-red-300",
  Cult: "bg-purple-900/50 text-purple-300",
  Animal: "bg-yellow-900/50 text-yellow-300",
  Space: "bg-indigo-900/50 text-indigo-300",
  Celebrity: "bg-pink-900/50 text-pink-300",
  Gaming: "bg-teal-900/50 text-teal-300",
};

export default function TokensPage() {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [chain, setChain] = useState("");
  const [snipeOnly, setSnipeOnly] = useState(false);

  function handleSearch(val: string) {
    setSearch(val);
    clearTimeout((handleSearch as any)._t);
    (handleSearch as any)._t = setTimeout(() => setDebouncedSearch(val), 300);
  }

  const { data: tokens, isLoading, error } = useSWR<DexToken[]>(
    ["/snipes/tokens", debouncedSearch, chain, snipeOnly],
    () =>
      api.snipes.tokens({
        search: debouncedSearch || undefined,
        chain: chain || undefined,
        snipe_only: snipeOnly || undefined,
        limit: 200,
      }),
    { refreshInterval: 60_000 }
  );

  return (
    <div className="space-y-4 pt-4">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-black uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
            DEX Tokens
          </h1>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-dim)" }}>
            {tokens != null ? `${tokens.length} tokens tracked` : "Loading…"}
            {" — "} DexScreener + Pump.fun
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="text"
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="Search symbol or name…"
          className="text-sm px-3 py-2 w-48 focus:outline-none"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            color: "var(--text-primary)",
          }}
        />
        <select
          value={chain}
          onChange={(e) => setChain(e.target.value)}
          className="text-sm px-3 py-2 focus:outline-none"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            color: "var(--text-secondary)",
          }}
        >
          <option value="">All Chains</option>
          <option value="solana">Solana</option>
          <option value="ethereum">Ethereum</option>
          <option value="bsc">BSC</option>
          <option value="base">Base</option>
        </select>
        <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: "var(--text-secondary)" }}>
          <input
            type="checkbox"
            checked={snipeOnly}
            onChange={(e) => setSnipeOnly(e.target.checked)}
            className="accent-indigo-500"
          />
          Snipe only
        </label>
      </div>

      {isLoading && (
        <div className="text-center py-16 text-sm" style={{ color: "var(--text-dim)" }}>
          Loading tokens…
        </div>
      )}
      {error && (
        <div className="p-4 text-sm border" style={{ background: "rgba(255,68,102,0.08)", borderColor: "rgba(255,68,102,0.3)", color: "var(--red)" }}>
          Failed to load. Is the API running?
        </div>
      )}
      {tokens && tokens.length === 0 && (
        <div className="text-center py-16 text-sm" style={{ color: "var(--text-dim)" }}>
          No tokens yet — the DEX worker is on its first scan. Check back in ~90s.
        </div>
      )}

      {tokens && tokens.length > 0 && (
        <div className="overflow-x-auto border" style={{ borderColor: "var(--border)" }}>
          <table className="min-w-full divide-y text-sm" style={{ borderColor: "var(--border)" }}>
            <thead style={{ background: "var(--bg-card)" }}>
              <tr>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: "var(--text-dim)" }}>Token</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden sm:table-cell" style={{ color: "var(--text-dim)" }}>Chain</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: "var(--text-dim)" }}>Score</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden md:table-cell" style={{ color: "var(--text-dim)" }}>Band</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: "var(--text-dim)" }}>Price</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden sm:table-cell" style={{ color: "var(--text-dim)" }}>5m%</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: "var(--text-dim)" }}>1h%</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden lg:table-cell" style={{ color: "var(--text-dim)" }}>Vol 5m</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden md:table-cell" style={{ color: "var(--text-dim)" }}>Liquidity</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden lg:table-cell" style={{ color: "var(--text-dim)" }}>MCap</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden xl:table-cell" style={{ color: "var(--text-dim)" }}>Age</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden md:table-cell" style={{ color: "var(--text-dim)" }}>Buy Press</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap hidden lg:table-cell" style={{ color: "var(--text-dim)" }}>Narrative</th>
                <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: "var(--text-dim)" }}>Snipe</th>
              </tr>
            </thead>
            <tbody style={{ background: "var(--bg-base)" }}>
              {tokens.map((t) => {
                const buys = t.buys_5m ?? 0;
                const sells = t.sells_5m ?? 0;
                const total = buys + sells;
                const bp = t.buy_pressure_pct ?? (total > 0 ? Math.round((buys / total) * 100) : null);
                const dot = BAND_DOT[t.band ?? ""] ?? "bg-gray-600";

                return (
                  <tr
                    key={`${t.chain}:${t.token_address}`}
                    className="transition-colors"
                    style={{ borderBottom: "1px solid var(--border)" }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-card)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        {t.image_url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={t.image_url} alt={t.symbol} width={20} height={20} className="shrink-0" />
                        ) : (
                          <div className="w-5 h-5 shrink-0" style={{ background: "var(--bg-card)" }} />
                        )}
                        <div>
                          <div className="font-bold" style={{ color: "var(--text-primary)" }}>{t.symbol}</div>
                          {t.name && <div className="text-xs truncate max-w-[80px]" style={{ color: "var(--text-dim)" }}>{t.name}</div>}
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-xs hidden sm:table-cell" style={{ color: "var(--text-secondary)" }}>
                      {CHAIN_LABELS[t.chain] ?? t.chain.toUpperCase()}
                      <div style={{ color: "var(--text-dim)" }}>{t.dex_id}</div>
                    </td>
                    <td className="px-3 py-2 mono font-bold" style={{ color: "var(--text-primary)" }}>
                      {t.snipe_score?.toFixed(1) ?? "—"}
                    </td>
                    <td className="px-3 py-2 hidden md:table-cell">
                      <div className="flex items-center gap-1.5">
                        <div className={`w-2 h-2 ${dot}`} />
                        <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{t.band ?? "—"}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2 mono" style={{ color: "var(--text-primary)" }}>{fmtPrice(t.price_usd)}</td>
                    <td className="px-3 py-2 hidden sm:table-cell"><PctCell v={t.price_change_5m} /></td>
                    <td className="px-3 py-2"><PctCell v={t.price_change_1h} /></td>
                    <td className="px-3 py-2 mono text-xs hidden lg:table-cell" style={{ color: "var(--text-secondary)" }}>{fmtCompact(t.volume_5m)}</td>
                    <td className="px-3 py-2 mono text-xs hidden md:table-cell" style={{ color: "var(--text-secondary)" }}>{fmtCompact(t.liquidity_usd)}</td>
                    <td className="px-3 py-2 mono text-xs hidden lg:table-cell" style={{ color: "var(--text-secondary)" }}>{fmtCompact(t.market_cap)}</td>
                    <td className="px-3 py-2 text-xs hidden xl:table-cell" style={{ color: "var(--text-secondary)" }}>{fmtAge(t.token_age_hours)}</td>
                    <td className="px-3 py-2 hidden md:table-cell">
                      {bp != null ? (
                        <span className="text-xs font-semibold" style={{ color: bp >= 60 ? "var(--green)" : bp >= 50 ? "var(--yellow)" : "var(--red)" }}>
                          {bp}%
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-dim)" }}>—</span>
                      )}
                    </td>
                    <td className="px-3 py-2 hidden lg:table-cell">
                      {t.narrative_category && (
                        <span className={`text-xs px-1.5 py-0.5 ${NARRATIVE_BADGE[t.narrative_category] ?? "bg-gray-800 text-gray-400"}`}>
                          {t.narrative_category}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {t.sniping_opportunity ? (
                        <span className="text-xs font-bold px-2 py-0.5" style={{ background: "rgba(0,217,126,0.15)", color: "var(--green)", border: "1px solid rgba(0,217,126,0.3)" }}>
                          YES
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-dim)" }}>—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
