'use client';

import type { MarketStatus, Signal, SectorFlow } from "@/types";
import { usePriceFlash } from "@/hooks/usePriceFlash";

interface TapeItemData {
  symbol: string;
  price?: string;        // optional — sectors have movement but no price
  pctChange: number;
}

interface Props {
  market: MarketStatus | null;
  signals: Signal[];
  sectorFlows: SectorFlow[];
}

// Backend can return change strings using a unicode minus ("−") instead of ASCII "-";
// normalize before parseFloat so we never get NaN on negative percentages.
function parsePct(s: string): number {
  const n = parseFloat(s.replace("−", "-"));
  return Number.isFinite(n) ? n : 0;
}

function buildTape(market: MarketStatus | null, signals: Signal[], sectorFlows: SectorFlow[]): TapeItemData[] {
  const out: TapeItemData[] = [];
  const seen = new Set<string>();

  if (market?.btcPrice) {
    out.push({ symbol: "BTC", price: market.btcPrice, pctChange: parsePct(market.btcChange) });
    seen.add("BTC");
  }
  if (market?.ethPrice) {
    out.push({ symbol: "ETH", price: market.ethPrice, pctChange: parsePct(market.ethChange) });
    seen.add("ETH");
  }

  // Tokens from active signals — only those with real (non-placeholder) prices.
  for (const sig of signals) {
    for (const t of sig.topTokens) {
      if (seen.has(t.symbol)) continue;
      if (!t.price || t.price === "—") continue;
      out.push({ symbol: t.symbol, price: t.price, pctChange: parsePct(t.change) });
      seen.add(t.symbol);
    }
  }

  // Sector flows — no price, but real movement data. Pull the strongest movers
  // by absolute change so the tape always crawls a varied mix.
  const sectors = [...sectorFlows].sort((a, b) => Math.abs(b.change) - Math.abs(a.change));
  for (const s of sectors) {
    const sym = s.name.toUpperCase();
    if (seen.has(sym)) continue;
    out.push({ symbol: sym, pctChange: s.change });
    seen.add(sym);
  }

  return out;
}

function TapeItem({ data }: { data: TapeItemData }) {
  const flash = usePriceFlash(data.price);
  return (
    <span className="tapeitem">
      <span className="tapesym">{data.symbol}</span>
      {data.price && (
        <span className={`text-terminal-muted px-0.5 ${flash}`}>{data.price}</span>
      )}
      <span className={data.pctChange >= 0 ? "text-terminal-green" : "text-terminal-red"}>
        {data.pctChange >= 0 ? "▲" : "▼"} {Math.abs(data.pctChange).toFixed(1)}%
      </span>
    </span>
  );
}

export default function TickerTape({ market, signals, sectorFlows }: Props) {
  const items = buildTape(market, signals, sectorFlows);

  // Render the row twice so the crawl translateX(-50%) loops seamlessly.
  // Flash only on the first copy — the second is a visual continuation.
  const renderRow = (suffix: string, flash: boolean) =>
    items.map((x, i) =>
      flash ? (
        <TapeItem key={`${suffix}-${x.symbol}-${i}`} data={x} />
      ) : (
        <span key={`${suffix}-${x.symbol}-${i}`} className="tapeitem">
          <span className="tapesym">{x.symbol}</span>
          {x.price && <span className="text-terminal-muted">{x.price}</span>}
          <span className={x.pctChange >= 0 ? "text-terminal-green" : "text-terminal-red"}>
            {x.pctChange >= 0 ? "▲" : "▼"} {Math.abs(x.pctChange).toFixed(1)}%
          </span>
        </span>
      )
    );

  return (
    <div className="tape" style={{ gridColumn: "1 / -1", gridRow: "2" }}>
      <div className="tapelabel">TAPE</div>
      <div className="tapeview">
        {items.length === 0 ? (
          <span className="tapeitem text-terminal-muted">CONNECTING...</span>
        ) : (
          <div className="tapetrack">
            {renderRow("a", true)}
            {renderRow("b", false)}
          </div>
        )}
      </div>
    </div>
  );
}
