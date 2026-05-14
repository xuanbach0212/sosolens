import type { ReactNode } from "react";
import type { MarketStatus } from "@/types";

interface Props {
  market: MarketStatus | null;
  isLoading: boolean;
  isError: boolean;
  isConnected: boolean;
  lastUpdated: Date | null;
  walletBar?: ReactNode;
}

export default function TopBar({ market, isLoading, isError, isConnected, lastUpdated, walletBar }: Props) {
  const statusLabel = isError
    ? <span className="text-terminal-red">● RECONNECTING · POLLING FALLBACK</span>
    : isConnected && lastUpdated
    ? <span className="text-terminal-green">● SSE LIVE · {lastUpdated.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'UTC' })} UTC</span>
    : isLoading
    ? <span className="text-terminal-yellow">● CONNECTING...</span>
    : <span className="text-terminal-muted">● SOSOVALUE API</span>;

  const dash = "—";

  return (
    <div
      className="border-b border-terminal-border bg-terminal-panel px-3 flex flex-col justify-center"
      style={{ gridColumn: "1 / -1" }}
    >
      <div className="flex items-center gap-6 text-xs">
        <span className="font-bold text-terminal-green tracking-widest">
          SOSOALPHA <span className="animate-pulse">●</span>LIVE
        </span>
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
          BTC <span className="text-terminal-text">{market?.btcPrice ?? dash}</span>{" "}
          <span className={market && parseFloat(market.btcChange) >= 0 ? "text-terminal-green" : "text-terminal-red"}>
            {market?.btcChange ?? ""}
          </span>
        </span>
        <span className="text-terminal-muted">│</span>
        <span>
          ETH <span className="text-terminal-text">{market?.ethPrice ?? dash}</span>{" "}
          <span className={market && parseFloat(market.ethChange) >= 0 ? "text-terminal-green" : "text-terminal-red"}>
            {market?.ethChange ?? ""}
          </span>
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
        <span>
          FEAR/GREED:{" "}
          {market ? (
            <span className="text-terminal-yellow">
              {market.fearGreed} {market.fearGreedLabel}
            </span>
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
