'use client';

import { useState } from "react";
import TopBar from "@/components/TopBar";
import SignalFeed from "@/components/SignalFeed";
import SignalDetail from "@/components/SignalDetail";
import MarketIntelligence from "@/components/MarketIntelligence";
import BottomBar from "@/components/BottomBar";
import WalletBar from "@/components/WalletBar";
import SubscribeModal from "@/components/SubscribeModal";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useWallet } from "@/hooks/useWallet";
import { useSubscription } from "@/hooks/useSubscription";

export default function Page() {
  const wallet = useWallet();
  const subscription = useSubscription(wallet.address);
  const [showModal, setShowModal] = useState(false);

  const {
    signals,
    stats,
    market,
    sectorFlows,
    etfFlows,
    macroStatus,
    riskEnvironment,
    btcTreasuries,
    vcActivity,
    aiBriefing,
    newsHeadlines,
    priceHistory,
    signalOutcomes,
    etfHistory,
    isDemoData,
    isLoading,
    isError,
    isConnected,
    lastUpdated,
  } = useDashboardData(wallet.address ?? undefined);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const effectiveId = selectedId ?? signals[0]?.id ?? null;
  const selectedSignal = signals.find((s) => s.id === effectiveId) ?? signals[0];

  // null = unknown (no wallet); false = free; true = premium
  const isPremium = wallet.address ? subscription.isSubscribed : null;

  return (
    <>
      <div
        className="h-screen overflow-hidden grid"
        style={{
          gridTemplateRows: "48px 1fr 90px",
          gridTemplateColumns: "220px 1fr 260px",
        }}
      >
        <TopBar
          market={market}
          isLoading={isLoading}
          isError={isError}
          isConnected={isConnected}
          lastUpdated={lastUpdated}
          priceHistory={priceHistory}
          riskEnvironment={riskEnvironment}
          isDemoData={isDemoData}
          walletBar={
            <WalletBar
              address={wallet.address}
              isSubscribed={subscription.isSubscribed}
              isConnecting={wallet.isConnecting}
              hasMetaMask={wallet.hasMetaMask}
              expiry={subscription.expiry}
              onConnect={wallet.connect}
              onUpgrade={() => setShowModal(true)}
            />
          }
        />
        <SignalFeed
          signals={signals}
          selectedId={effectiveId ?? ""}
          onSelect={setSelectedId}
          stats={stats}
          isLoading={isLoading}
          isPremium={isPremium}
          signalOutcomes={signalOutcomes}
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
          etfHistory={etfHistory}
        />
        <BottomBar briefing={aiBriefing} news={newsHeadlines} lastUpdated={lastUpdated} />
      </div>

      <SubscribeModal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false);
          subscription.reset();
        }}
        isSubscribed={subscription.isSubscribed}
        step={subscription.step}
        error={subscription.error}
        expiry={subscription.expiry}
        onSubscribe={subscription.subscribe}
        onReset={subscription.reset}
      />
    </>
  );
}
