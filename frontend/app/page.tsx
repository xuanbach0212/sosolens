'use client';

import { useState } from "react";
import TopBar from "@/components/TopBar";
import SignalFeed from "@/components/SignalFeed";
import SignalDetail from "@/components/SignalDetail";
import MarketIntelligence from "@/components/MarketIntelligence";
import BottomBar from "@/components/BottomBar";
import { useDashboardData } from "@/hooks/useDashboardData";

export default function Page() {
  const {
    signals,
    stats,
    market,
    sectorFlows,
    etfFlows,
    macroStatus,
    btcTreasuries,
    vcActivity,
    aiBriefing,
    newsHeadlines,
    isLoading,
    isError,
    isConnected,
    lastUpdated,
  } = useDashboardData();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const effectiveId = selectedId ?? signals[0]?.id ?? null;
  const selectedSignal = signals.find((s) => s.id === effectiveId) ?? signals[0];

  return (
    <div
      className="h-screen overflow-hidden grid"
      style={{
        gridTemplateRows: "48px 1fr 90px",
        gridTemplateColumns: "220px 1fr 260px",
      }}
    >
      <TopBar market={market} isLoading={isLoading} isError={isError} isConnected={isConnected} lastUpdated={lastUpdated} />
      <SignalFeed
        signals={signals}
        selectedId={effectiveId ?? ""}
        onSelect={setSelectedId}
        stats={stats}
        isLoading={isLoading}
      />
      {selectedSignal ? (
        <SignalDetail signal={selectedSignal} />
      ) : (
        <div
          className="border-r border-terminal-border flex items-center justify-center text-terminal-muted text-[10px] tracking-widest"
          style={{ gridColumn: "2", gridRow: "2" }}
        >
          {isLoading ? "CONNECTING TO AGENT..." : "AGENT RUNNING · FIRST SIGNALS IN ~60s"}
        </div>
      )}
      <MarketIntelligence
        sectorFlows={sectorFlows}
        etfFlows={etfFlows}
        macroStatus={macroStatus}
        btcTreasuries={btcTreasuries}
        vcActivity={vcActivity}
      />
      <BottomBar briefing={aiBriefing} news={newsHeadlines} lastUpdated={lastUpdated} />
    </div>
  );
}
