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

  if (!selectedSignal) {
    return (
      <div className="h-screen flex items-center justify-center text-terminal-muted text-xs tracking-widest">
        LOADING...
      </div>
    );
  }

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
        selectedId={effectiveId ?? signals[0].id}
        onSelect={setSelectedId}
        stats={stats}
      />
      <SignalDetail signal={selectedSignal} />
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
