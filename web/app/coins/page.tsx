"use client";

import { useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Coin } from "@/types";

export const dynamic = "force-dynamic";

function fmtPrice(n: number | null | undefined): string {
  if (n == null) return "—";
  if (n < 0.000001) return `$${n.toExponential(3)}`;
  if (n < 0.01) return `$${n.toFixed(6)}`;
  if (n < 1) return `$${n.toFixed(4)}`;
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function fmtLarge(n: number | null | undefined): string {
  if (n == null) return "—";
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(2)}K`;
  return `$${n.toFixed(2)}`;
}

function PctChange({ value }: { value: number | null }) {
  if (value == null) return <span style={{ color: "var(--text-dim)" }}>—</span>;
  const pos = value >= 0;
  return (
    <span style={{ color: pos ? "var(--green)" : "var(--red)" }} className="font-semibold mono">
      {pos ? "+" : ""}{value.toFixed(2)}%
    </span>
  );
}

export default function CoinsPage() {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  function handleSearch(value: string) {
    setSearch(value);
    clearTimeout((handleSearch as any)._t);
    (handleSearch as any)._t = setTimeout(() => setDebouncedSearch(value), 300);
  }

  const { data: coins, isLoading, error } = useSWR<Coin[]>(
    ["/coins/", debouncedSearch],
    () => api.coins.list({ search: debouncedSearch || undefined, limit: 500 }),
    { refreshInterval: 120_000 }
  );

  return (
    <div className="space-y-4 pt-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-black uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
            Meme Coins
          </h1>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-dim)" }}>
            {coins != null
              ? `${coins.length.toLocaleString()} coins tracked — sorted by market cap rank`
              : "Loading market data…"}
          </p>
        </div>
        <input
          type="text"
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="Search symbol or name…"
          className="text-sm px-3 py-2 w-56 focus:outline-none"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            color: "var(--text-primary)",
          }}
        />
      </div>

      {isLoading && (
        <div className="text-center py-16 text-sm" style={{ color: "var(--text-dim)" }}>
          Loading coins…
        </div>
      )}
      {error && (
        <div className="p-4 text-sm border" style={{ background: "rgba(255,68,102,0.08)", borderColor: "rgba(255,68,102,0.3)", color: "var(--red)" }}>
          Failed to load coins. Is the API running? The worker may still be fetching data.
        </div>
      )}
      {coins && coins.length === 0 && (
        <div className="text-center py-16 text-sm" style={{ color: "var(--text-dim)" }}>
          {debouncedSearch
            ? `No coins match "${debouncedSearch}".`
            : "No coins yet — the worker is fetching market data from CoinGecko. Check back shortly."}
        </div>
      )}

      {coins && coins.length > 0 && (
        <div className="overflow-x-auto border" style={{ borderColor: "var(--border)" }}>
          <table className="min-w-full divide-y text-sm" style={{ borderColor: "var(--border)" }}>
            <thead style={{ background: "var(--bg-card)" }}>
              <tr>
                {["#", "Coin", "Price", "24h %", "7d %", "Market Cap", "Volume 24h", "Supply", ""].map((h) => (
                  <th
                    key={h}
                    className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider whitespace-nowrap"
                    style={{ color: "var(--text-dim)" }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody style={{ background: "var(--bg-base)" }}>
              {coins.map((c) => (
                <tr
                  key={c.id}
                  className="transition-colors"
                  style={{ borderBottom: "1px solid var(--border)" }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-card)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <td className="px-3 py-2.5 text-xs mono" style={{ color: "var(--text-dim)" }}>
                    {c.market_cap_rank ?? "—"}
                  </td>
                  <td className="px-3 py-2.5">
                    <div className="flex items-center gap-2">
                      {c.image_url && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={c.image_url} alt={c.symbol} width={22} height={22} className="shrink-0" />
                      )}
                      <div>
                        <div className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>{c.symbol}</div>
                        <div className="text-xs truncate max-w-[120px]" style={{ color: "var(--text-dim)" }}>{c.name}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-2.5 mono text-sm" style={{ color: "var(--text-primary)" }}>
                    {fmtPrice(c.price_usd)}
                  </td>
                  <td className="px-3 py-2.5 mono">
                    <PctChange value={c.price_change_24h} />
                  </td>
                  <td className="px-3 py-2.5 mono hidden sm:table-cell">
                    <PctChange value={c.price_change_7d} />
                  </td>
                  <td className="px-3 py-2.5 mono text-xs hidden md:table-cell" style={{ color: "var(--text-secondary)" }}>
                    {fmtLarge(c.market_cap_usd)}
                  </td>
                  <td className="px-3 py-2.5 mono text-xs hidden lg:table-cell" style={{ color: "var(--text-secondary)" }}>
                    {fmtLarge(c.volume_24h_usd)}
                  </td>
                  <td className="px-3 py-2.5 mono text-xs hidden xl:table-cell" style={{ color: "var(--text-dim)" }}>
                    {c.circulating_supply != null
                      ? `${(c.circulating_supply / 1e9).toFixed(2)}B ${c.symbol}`
                      : "—"}
                  </td>
                  <td className="px-3 py-2.5">
                    <Link
                      href={`/coins/${c.symbol}`}
                      className="text-xs px-2 py-1 font-medium whitespace-nowrap"
                      style={{ background: "rgba(68,136,255,0.12)", color: "var(--blue)", border: "1px solid rgba(68,136,255,0.25)" }}
                    >
                      Details →
                    </Link>
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
