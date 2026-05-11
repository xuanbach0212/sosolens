import type { SectorFlow, EtfFlow, MacroItem, BtcTreasury, VcActivity } from "@/types";

interface Props {
  sectorFlows: SectorFlow[];
  etfFlows: EtfFlow[];
  macroStatus: MacroItem[];
  btcTreasuries: BtcTreasury[];
  vcActivity: VcActivity[];
}

function PanelHeader({ title }: { title: string }) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <span className="text-[10px] font-bold text-terminal-muted tracking-widest whitespace-nowrap">
        {title}
      </span>
      <div className="flex-1 border-t border-terminal-border" />
    </div>
  );
}

const MAX_FLOW = 40;

export default function MarketIntelligence({
  sectorFlows,
  etfFlows,
  macroStatus,
  btcTreasuries,
  vcActivity,
}: Props) {
  return (
    <div
      className="flex flex-col overflow-y-auto px-3 py-3 space-y-4"
      style={{ gridColumn: "3", gridRow: "2" }}
    >
      {/* Sector Flows */}
      <div>
        <PanelHeader title="SECTOR FLOWS (7D)" />
        {sectorFlows.length === 0 && (
          <div className="text-[10px] text-terminal-muted italic">Loading...</div>
        )}
        <div className="space-y-0.5">
          {sectorFlows.map((s) => {
            const pct = Math.abs(s.change) / MAX_FLOW;
            const width = Math.max(pct * 100, 2);
            const positive = s.change >= 0;
            return (
              <div key={s.name} className="flex items-center gap-1.5">
                <span className="text-[10px] text-terminal-muted w-12 shrink-0">{s.name}</span>
                <div className="flex-1 h-2 bg-terminal-border rounded-sm overflow-hidden">
                  <div
                    className={`h-full rounded-sm ${positive ? "bg-terminal-green" : "bg-terminal-red"}`}
                    style={{ width: `${width}%` }}
                  />
                </div>
                <span
                  className={`text-[10px] w-10 text-right shrink-0 ${
                    positive ? "text-terminal-green" : "text-terminal-red"
                  }`}
                >
                  {positive ? "+" : ""}
                  {s.change}%
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* ETF Flows */}
      <div>
        <PanelHeader title="ETF FLOWS (24H)" />
        {etfFlows.length === 0 && (
          <div className="text-[10px] text-terminal-muted italic">Loading...</div>
        )}
        <div className="space-y-0.5">
          {etfFlows.map((e) => (
            <div
              key={e.name}
              className={`flex justify-between text-[10px] ${
                e.total ? "border-t border-terminal-border pt-1 mt-1 font-bold" : ""
              }`}
            >
              <span className="text-terminal-muted">{e.name}</span>
              <span className={e.positive ? "text-terminal-green" : "text-terminal-red"}>
                {e.flow} {e.arrows}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Macro Status */}
      <div>
        <PanelHeader title="MACRO STATUS" />
        {macroStatus.length === 0 && (
          <div className="text-[10px] text-terminal-muted italic">Loading...</div>
        )}
        <div className="space-y-0.5">
          {macroStatus.map((m) => (
            <div key={m.name} className="flex justify-between text-[10px]">
              <span className="text-terminal-muted">{m.name}</span>
              <span className={m.warning ? "text-terminal-yellow" : "text-terminal-text"}>
                {m.value} {m.arrow}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* BTC Treasuries */}
      <div>
        <PanelHeader title="BTC TREASURIES" />
        {btcTreasuries.length === 0 && (
          <div className="text-[10px] text-terminal-muted italic">Loading...</div>
        )}
        <div className="space-y-1">
          {btcTreasuries.map((t) => (
            <div key={t.company}>
              <div className="text-[10px] text-terminal-text">{t.company}</div>
              <div className="flex justify-between text-[10px]">
                <span className="text-terminal-muted">{t.btcHeld}</span>
                <span
                  className={
                    t.positive === true
                      ? "text-terminal-green"
                      : t.positive === false
                      ? "text-terminal-red"
                      : "text-terminal-muted"
                  }
                >
                  {t.weeklyChange}{" "}
                  {t.positive === true ? "↑" : t.positive === false ? "↓" : "⚪"}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* VC Activity */}
      <div>
        <PanelHeader title="VC ACTIVITY (7D)" />
        {vcActivity.length === 0 && (
          <div className="text-[10px] text-terminal-muted italic">Loading...</div>
        )}
        <div className="space-y-0.5">
          {vcActivity.map((v) => (
            <div key={v.sector} className="flex justify-between text-[10px]">
              <span className="text-terminal-muted">{v.sector}</span>
              <span className="text-terminal-text">
                {v.rounds} round{v.rounds !== 1 ? "s" : ""}{" "}
                <span className="text-terminal-green">{v.totalUsd}</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
