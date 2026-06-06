import { useEffect, useState } from "react";
import type { SectorFlow, EtfFlow, MacroItem, BtcTreasury, VcActivity, EtfFlowSnapshot, MacroEvent } from "@/types";

interface Props {
  sectorFlows: SectorFlow[];
  etfFlows: EtfFlow[];
  macroStatus: MacroItem[];
  btcTreasuries: BtcTreasury[];
  vcActivity: VcActivity[];
  etfHistory?: EtfFlowSnapshot[];
  upcomingEvents?: MacroEvent[];
  agentRunTick: number;
}

function PanelHeader({ title }: { title: string }) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <span className="text-[10px] font-bold text-terminal-muted tracking-widest whitespace-nowrap">
        {title}
      </span>
      <div className="flex-1 border-t border-terminal-bordersoft" />
    </div>
  );
}

const MAX_FLOW = 40;

function sectorFlowStyle(change: number): { bg: string; textClass: string } {
  const intensity = Math.min(Math.abs(change) / MAX_FLOW, 1);
  const alpha = 0.15 + intensity * 0.65;
  if (change > 0) {
    return { bg: `rgba(0, 255, 136, ${alpha.toFixed(2)})`, textClass: "text-terminal-green" };
  }
  if (change < 0) {
    return { bg: `rgba(255, 68, 68, ${alpha.toFixed(2)})`, textClass: "text-terminal-red" };
  }
  return { bg: "rgba(255,255,255,0.04)", textClass: "text-terminal-muted" };
}

function EtfBarChart({ data, width = 120, height = 22 }: { data: number[]; width?: number; height?: number }) {
  if (data.length === 0) return null;
  const BUCKETS = 7;
  const bucketSize = Math.ceil(data.length / BUCKETS);
  const buckets: number[] = [];
  for (let i = 0; i < data.length; i += bucketSize) {
    const slice = data.slice(i, i + bucketSize);
    buckets.push(slice.reduce((s, v) => s + v, 0) / slice.length);
  }
  const maxAbs = Math.max(...buckets.map((v) => Math.abs(v)), 1);
  const gap = 2;
  const barW = (width - gap * (buckets.length - 1)) / buckets.length;
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {buckets.map((v, i) => {
        const normalized = Math.abs(v) / maxAbs;
        const barH = Math.max(2, normalized * (height - 2));
        const x = i * (barW + gap);
        const y = height - barH;
        const fillVar = v >= 0 ? "var(--color-terminal-green)" : "var(--color-terminal-red)";
        return <rect key={i} x={x} y={y} width={Math.max(1, barW)} height={barH} style={{ fill: fillVar }} opacity={0.75} />;
      })}
    </svg>
  );
}

export default function MarketIntelligence({
  sectorFlows,
  etfFlows,
  macroStatus,
  btcTreasuries,
  vcActivity,
  etfHistory = [],
  upcomingEvents = [],
  agentRunTick,
}: Props) {
  const [pulse, setPulse] = useState(false);
  useEffect(() => {
    if (agentRunTick === 0) return;
    setPulse(true);
    const t = setTimeout(() => setPulse(false), 1500);
    return () => clearTimeout(t);
  }, [agentRunTick]);
  const panelCls = pulse ? "sync-pulse" : "";

  return (
    <div
      className="flex flex-col overflow-y-auto px-3 py-3 space-y-4"
      style={{ gridColumn: "3", gridRow: "3" }}
    >
      {/* Sector Flows */}
      <div className={panelCls}>
        <PanelHeader title="SECTOR FLOWS · 7D" />
        {sectorFlows.length === 0 && (
          <div className="text-[10px] text-terminal-muted italic">Loading...</div>
        )}
        <div className="grid grid-cols-3 gap-1">
          {sectorFlows.map((s) => {
            const { bg, textClass } = sectorFlowStyle(s.change);
            const positive = s.change > 0;
            return (
              <div
                key={s.name}
                className="rounded px-1.5 py-1.5 flex flex-col gap-0.5"
                style={{ backgroundColor: bg }}
              >
                <span className="text-[9px] text-terminal-muted leading-none truncate">{s.name}</span>
                <span className={`text-[10px] font-bold leading-none ${textClass}`}>
                  {positive ? "+" : ""}{s.change}%
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* ETF Flows */}
      <div className={panelCls}>
        <PanelHeader title="ETF FLOWS · 7D" />
        {etfFlows.length === 0 && (
          <div className="text-[10px] text-terminal-muted italic">Loading...</div>
        )}
        <div className="space-y-0.5">
          {etfFlows.map((e) => (
            <div key={e.name}>
              <div
                className={`flex justify-between text-[10px] ${
                  e.total ? "border-t border-terminal-border pt-1 mt-1 font-bold" : ""
                }`}
              >
                <span className="text-terminal-muted">{e.name}</span>
                <span className={e.positive ? "text-terminal-green" : "text-terminal-red"}>
                  {e.flow} {e.arrows}
                </span>
              </div>
              {!e.total && etfHistory.length > 0 && (
                <div className="mt-0.5 mb-1">
                  <EtfBarChart
                    data={e.name === "BTC ETF"
                      ? etfHistory.map((s) => s.btcFlow)
                      : etfHistory.map((s) => s.ethFlow)}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Macro Status */}
      <div className={panelCls}>
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
      <div className={panelCls}>
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

      {/* Upcoming Events */}
      {upcomingEvents.length > 0 && (
        <div className={panelCls}>
          <PanelHeader title="UPCOMING EVENTS · 14D" />
          <div className="space-y-0.5">
            {upcomingEvents.slice(0, 6).map((e, i) => {
              const label = e.events.slice(0, 2).join(", ");
              const when = e.days_until === 0 ? "today" : `in ${e.days_until}d`;
              return (
                <div key={i} className="flex justify-between text-[10px]">
                  <span className="text-terminal-muted truncate mr-2 flex-1">{label}</span>
                  <span className={e.high_impact && e.days_until <= 7 ? "text-terminal-yellow shrink-0" : "text-terminal-text shrink-0"}>
                    {when}{e.high_impact && e.days_until <= 7 ? " ⚠" : ""}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* VC Activity — funding-round mentions parsed from the news feed,
          not a real VC-round dataset, so labelled accordingly. */}
      <div className={panelCls}>
        <PanelHeader title="FUNDING MENTIONS" />
        <div className="text-[9px] text-terminal-muted/70 italic -mt-1 mb-1">
          from news headlines
        </div>
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
