'use client';

import { useState } from "react";
import TopBar from "@/components/TopBar";
import SignalFeed from "@/components/SignalFeed";
import SignalDetail from "@/components/SignalDetail";
import MarketIntelligence from "@/components/MarketIntelligence";
import BottomBar from "@/components/BottomBar";
import {
  signals,
  signalStats,
  marketStatus,
  sectorFlows,
  etfFlows,
  macroStatus,
  btcTreasuries,
  vcActivity,
  aiBriefing,
  newsHeadlines,
} from "@/data/dummy";

export default function Page() {
  const [selectedId, setSelectedId] = useState(signals[0].id);
  const selectedSignal = signals.find((s) => s.id === selectedId) ?? signals[0];

  return (
    <div
      className="h-screen overflow-hidden grid"
      style={{
        gridTemplateRows: "48px 1fr 90px",
        gridTemplateColumns: "220px 1fr 260px",
      }}
    >
      <TopBar market={marketStatus} />
      <SignalFeed
        signals={signals}
        selectedId={selectedId}
        onSelect={setSelectedId}
        stats={signalStats}
      />
      <SignalDetail signal={selectedSignal} />
      <MarketIntelligence
        sectorFlows={sectorFlows}
        etfFlows={etfFlows}
        macroStatus={macroStatus}
        btcTreasuries={btcTreasuries}
        vcActivity={vcActivity}
      />
      <BottomBar briefing={aiBriefing} news={newsHeadlines} />
    </div>
  );
}
