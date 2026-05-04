import { MarketStatus } from "@/data/dummy";

interface Props {
  market: MarketStatus;
}

export default function TopBar({ market }: Props) {
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
          <span className={market.sentimentPositive ? "text-terminal-green" : "text-terminal-red"}>
            {market.sentimentPositive ? "🟢" : "🔴"} {market.sentiment}
          </span>
        </span>
        <span className="text-terminal-muted">│</span>
        <span>
          BTC <span className="text-terminal-text">{market.btcPrice}</span>{" "}
          <span className="text-terminal-green">{market.btcChange}</span>
        </span>
        <span className="text-terminal-muted">│</span>
        <span>
          ETH <span className="text-terminal-text">{market.ethPrice}</span>{" "}
          <span className="text-terminal-green">{market.ethChange}</span>
        </span>
        <span className="text-terminal-muted">│</span>
        <span>
          MCAP <span className="text-terminal-text">{market.mcap}</span>{" "}
          <span className="text-terminal-green">{market.mcapChange}</span>
        </span>
        <span className="text-terminal-muted">│</span>
        <span>
          VOL <span className="text-terminal-text">{market.vol}</span>{" "}
          <span className="text-terminal-green">{market.volChange}</span>
        </span>
        <span className="text-terminal-muted">│</span>
        <span>
          FEAR/GREED:{" "}
          <span className="text-terminal-yellow">
            {market.fearGreed} {market.fearGreedLabel}
          </span>
        </span>
        <span className="ml-auto text-terminal-muted text-[10px]">
          DATA: SOSOVALUE API · MOCKUP
        </span>
      </div>
    </div>
  );
}
