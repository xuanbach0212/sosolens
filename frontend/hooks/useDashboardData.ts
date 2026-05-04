'use client';

import { useState, useEffect, useCallback } from 'react';
import type {
  Signal,
  SignalStats,
  MarketStatus,
  SectorFlow,
  EtfFlow,
  MacroItem,
  BtcTreasury,
  VcActivity,
  NewsHeadline,
} from '@/types';
import {
  signals as fallbackSignals,
  signalStats as fallbackStats,
  marketStatus as fallbackMarket,
  sectorFlows as fallbackSectorFlows,
  etfFlows as fallbackEtfFlows,
  macroStatus as fallbackMacro,
  btcTreasuries as fallbackBtcTreasuries,
  vcActivity as fallbackVcActivity,
  aiBriefing as fallbackAiBriefing,
  newsHeadlines as fallbackNewsHeadlines,
} from '@/data/dummy';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const REFRESH_INTERVAL_MS = 60_000;

export interface DashboardData {
  signals: Signal[];
  stats: SignalStats;
  market: MarketStatus;
  sectorFlows: SectorFlow[];
  etfFlows: EtfFlow[];
  macroStatus: MacroItem[];
  btcTreasuries: BtcTreasury[];
  vcActivity: VcActivity[];
  aiBriefing: string[];
  newsHeadlines: NewsHeadline[];
  isLoading: boolean;
  isError: boolean;
  lastUpdated: Date | null;
  refresh: () => void;
}

export function useDashboardData(): DashboardData {
  const [signals, setSignals] = useState<Signal[]>(fallbackSignals);
  const [stats, setStats] = useState<SignalStats>(fallbackStats);
  const [market, setMarket] = useState<MarketStatus>(fallbackMarket);
  const [sectorFlows, setSectorFlows] = useState<SectorFlow[]>(fallbackSectorFlows);
  const [etfFlows, setEtfFlows] = useState<EtfFlow[]>(fallbackEtfFlows);
  const [macroStatus, setMacroStatus] = useState<MacroItem[]>(fallbackMacro);
  const [btcTreasuries, setBtcTreasuries] = useState<BtcTreasury[]>(fallbackBtcTreasuries);
  const [vcActivity, setVcActivity] = useState<VcActivity[]>(fallbackVcActivity);
  const [aiBriefing, setAiBriefing] = useState<string[]>(fallbackAiBriefing);
  const [newsHeadlines, setNewsHeadlines] = useState<NewsHeadline[]>(fallbackNewsHeadlines);
  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchAll = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);
    try {
      const [sigRes, mktRes, secRes, etfRes, macRes, btcRes, vcRes, newsRes] =
        await Promise.all([
          fetch(`${API_BASE}/api/signals`),
          fetch(`${API_BASE}/api/market`),
          fetch(`${API_BASE}/api/sector-flows`),
          fetch(`${API_BASE}/api/etf-flows`),
          fetch(`${API_BASE}/api/macro`),
          fetch(`${API_BASE}/api/btc-treasuries`),
          fetch(`${API_BASE}/api/vc-activity`),
          fetch(`${API_BASE}/api/news`),
        ]);

      if (!sigRes.ok || !mktRes.ok) throw new Error('fetch failed');

      const [sigData, mktData, secData, etfData, macData, btcData, vcData, newsData] =
        await Promise.all([
          sigRes.json(), mktRes.json(), secRes.json(), etfRes.json(),
          macRes.json(), btcRes.json(), vcRes.json(), newsRes.json(),
        ]);

      setSignals(sigData.signals);
      setStats(sigData.stats);
      setMarket(mktData.market);
      setSectorFlows(secData.sectorFlows);
      setEtfFlows(etfData.etfFlows);
      setMacroStatus(macData.macroStatus);
      setBtcTreasuries(btcData.btcTreasuries);
      setVcActivity(vcData.vcActivity);
      setAiBriefing(newsData.aiBriefing);
      setNewsHeadlines(newsData.newsHeadlines);
      setLastUpdated(new Date());
    } catch {
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, REFRESH_INTERVAL_MS);
    return () => clearInterval(id);
  }, [fetchAll]);

  return {
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
    lastUpdated,
    refresh: fetchAll,
  };
}
