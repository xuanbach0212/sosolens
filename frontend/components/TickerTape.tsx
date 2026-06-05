'use client';

import type { MarketStatus, Signal } from "@/types";

interface TapeItem {
  symbol: string;
  price: string;
  pctChange: number;
}

interface Props {
  market: MarketStatus | null;
  signals: Signal[];
}

// Backend can return change strings using a unicode minus ("−") instead of ASCII "-";
// normalize before parseFloat so we never get NaN on negative percentages.
function parsePct(s: string): number {
  const n = parseFloat(s.replace("−", "-"));
  return Number.isFinite(n) ? n : 0;
}

function buildTape(market: MarketStatus | null, signals: Signal[]): TapeItem[] {
  const out: TapeItem[] = [];
  const seen = new Set<string>();

  if (market?.btcPrice) {
    out.push({ symbol: "BTC", price: market.btcPrice, pctChange: parsePct(market.btcChange) });
    seen.add("BTC");
  }
  if (market?.ethPrice) {
    out.push({ symbol: "ETH", price: market.ethPrice, pctChange: parsePct(market.ethChange) });
    seen.add("ETH");
  }

  for (const sig of signals) {
    for (const t of sig.topTokens) {
      if (seen.has(t.symbol)) continue;
      if (!t.price || t.price === "—") continue;
      out.push({ symbol: t.symbol, price: t.price, pctChange: parsePct(t.change) });
      seen.add(t.symbol);
    }
  }

  return out;
}

export default function TickerTape({ market, signals }: Props) {
  const items = buildTape(market, signals);

  // Render the row twice so the crawl translateX(-50%) loops seamlessly.
  const renderRow = (suffix: string) =>
    items.map((x, i) => (
      <span key={`${suffix}-${x.symbol}-${i}`} className="tapeitem">
        <span className="tapesym">{x.symbol}</span>
        <span className="text-terminal-muted">{x.price}</span>
        <span className={x.pctChange >= 0 ? "text-terminal-green" : "text-terminal-red"}>
          {x.pctChange >= 0 ? "▲" : "▼"} {Math.abs(x.pctChange).toFixed(1)}%
        </span>
      </span>
    ));

  return (
    <div className="tape" style={{ gridColumn: "1 / -1", gridRow: "2" }}>
      <div className="tapelabel">TAPE</div>
      <div className="tapeview">
        {items.length === 0 ? (
          <span className="tapeitem text-terminal-muted">CONNECTING...</span>
        ) : (
          <div className="tapetrack">
            {renderRow("a")}
            {renderRow("b")}
          </div>
        )}
      </div>
    </div>
  );
}
