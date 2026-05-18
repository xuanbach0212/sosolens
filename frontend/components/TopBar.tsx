import { useRef } from "react";
import type { CSSProperties, ReactNode } from "react";
import type { MarketStatus, PriceSnapshot } from "@/types";

function fearGreedDisplay(v: number): { className: string; style?: CSSProperties } {
  if (v <= 24) return { className: "text-terminal-red" };
  if (v <= 44) return { className: "", style: { color: "#f97316" } };
  if (v <= 55) return { className: "text-terminal-yellow" };
  if (v <= 74) return { className: "text-terminal-green" };
  return { className: "text-terminal-green font-bold" };
}

function macroRegimeDisplay(regime: string): { label: string; className: string } {
  if (regime === "risk-off") return { label: "RISK-OFF ⚠", className: "text-terminal-red" };
  if (regime === "risk-on")  return { label: "RISK-ON",    className: "text-terminal-green" };
  return                            { label: "NEUTRAL",    className: "text-terminal-yellow" };
}

function Sparkline({ data, color }: { data: number[]; color: string }) {
  if (data.length < 2) return null;
  const w = 50, h = 18;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const step = Math.max(1, Math.floor(data.length / 60));
  const pts = data.filter((_, i) => i % step === 0);
  const points = pts
    .map((v, i) => `${(i / (pts.length - 1)) * w},${h - ((v - min) / range) * h}`)
    .join(" ");
  return (
    <svg width={w} height={h} style={{ display: "inline-block", verticalAlign: "middle" }}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.2" />
    </svg>
  );
}

interface Props {
  market: MarketStatus | null;
  isLoading: boolean;
  isError: boolean;
  isConnected: boolean;
  lastUpdated: Date | null;
  walletBar?: ReactNode;
  priceHistory: PriceSnapshot[];
  riskEnvironment: string;
  isDemoData?: boolean;
}

export default function TopBar({ market, isLoading, isError, isConnected, lastUpdated, walletBar, priceHistory, riskEnvironment, isDemoData }: Props) {
  const prevFearGreed = useRef<number | null>(null);

  const statusLabel = isError
    ? <span className="text-terminal-red">● RECONNECTING · POLLING FALLBACK</span>
    : isConnected && lastUpdated
    ? <span className="text-terminal-green">● SSE LIVE · {lastUpdated.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'UTC' })} UTC</span>
    : isLoading
    ? <span className="text-terminal-yellow">● CONNECTING...</span>
    : <span className="text-terminal-muted">● SOSOVALUE API</span>;

  const dash = "—";

  const fearGreedTrend = market && prevFearGreed.current !== null && market.fearGreed !== prevFearGreed.current
    ? market.fearGreed > prevFearGreed.current ? "↑" : "↓"
    : null;
  if (market) prevFearGreed.current = market.fearGreed;

  const btcData = priceHistory.map(p => p.btcPrice);
  const ethData = priceHistory.map(p => p.ethPrice);
  const btcSparkColor = btcData.length >= 2 && btcData[btcData.length - 1] >= btcData[0]
    ? "var(--color-terminal-green)" : "var(--color-terminal-red)";
  const ethSparkColor = ethData.length >= 2 && ethData[ethData.length - 1] >= ethData[0]
    ? "var(--color-terminal-green)" : "var(--color-terminal-red)";

  return (
    <div
      className="border-b border-terminal-border bg-terminal-panel px-3 flex flex-col justify-center"
      style={{ gridColumn: "1 / -1" }}
    >
      <div className="flex items-center gap-6 text-xs">
        <span className="font-bold text-terminal-green tracking-widest">
          SOSOLENS <span className="animate-pulse">●</span>LIVE
        </span>
        {isDemoData && (
          <span className="text-terminal-yellow text-xs border border-terminal-yellow px-1 tracking-wider">
            DEMO DATA
          </span>
        )}
        <span className="text-terminal-muted">│</span>
        <span>
          MARKET:{" "}
          {market ? (
            <span className={market.sentimentPositive ? "text-terminal-green" : "text-terminal-red"}>
              {market.sentimentPositive ? "🟢" : "🔴"} {market.sentiment}
            </span>
          ) : (
            <span className="text-terminal-muted">{dash}</span>
          )}
        </span>
        <span className="text-terminal-muted">│</span>
        <span>
          MACRO:{" "}
          <span className={macroRegimeDisplay(riskEnvironment).className}>
            {macroRegimeDisplay(riskEnvironment).label}
          </span>
        </span>
        <span className="text-terminal-muted">│</span>
        <span className="flex items-center gap-1">
          BTC <span className="text-terminal-text">{market?.btcPrice ?? dash}</span>{" "}
          <span className={market && parseFloat(market.btcChange) >= 0 ? "text-terminal-green" : "text-terminal-red"}>
            {market?.btcChange ?? ""}
          </span>
          <Sparkline data={btcData} color={btcSparkColor} />
        </span>
        <span className="text-terminal-muted">│</span>
        <span className="flex items-center gap-1">
          ETH <span className="text-terminal-text">{market?.ethPrice ?? dash}</span>{" "}
          <span className={market && parseFloat(market.ethChange) >= 0 ? "text-terminal-green" : "text-terminal-red"}>
            {market?.ethChange ?? ""}
          </span>
          <Sparkline data={ethData} color={ethSparkColor} />
        </span>
        <span className="text-terminal-muted">│</span>
        <span>
          MCAP <span className="text-terminal-text">{market?.mcap ?? dash}</span>{" "}
          <span className="text-terminal-green">{market?.mcapChange ?? ""}</span>
        </span>
        <span className="text-terminal-muted">│</span>
        <span>
          VOL <span className="text-terminal-text">{market?.vol ?? dash}</span>{" "}
          <span className="text-terminal-green">{market?.volChange ?? ""}</span>
        </span>
        <span className="text-terminal-muted">│</span>
        <span className="flex items-center gap-1">
          FEAR/GREED:{" "}
          {market ? (
            <>
              <span className={fearGreedDisplay(market.fearGreed).className} style={fearGreedDisplay(market.fearGreed).style}>
                {market.fearGreed}
              </span>
              {fearGreedTrend && (
                <span className={fearGreedTrend === "↑" ? "text-terminal-green" : "text-terminal-red"}>
                  {fearGreedTrend}
                </span>
              )}
              <span className="text-terminal-muted">{market.fearGreedLabel}</span>
            </>
          ) : (
            <span className="text-terminal-muted">{dash}</span>
          )}
        </span>
        <span className="ml-auto flex items-center gap-3 text-[10px]">
          {statusLabel}
          {walletBar && (
            <>
              <span className="text-terminal-muted">│</span>
              {walletBar}
            </>
          )}
        </span>
      </div>
    </div>
  );
}
