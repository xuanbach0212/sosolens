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

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const REFRESH_INTERVAL_MS = 60_000;

export interface DashboardData {
  signals: Signal[];
  stats: SignalStats;
  market: MarketStatus | null;
  sectorFlows: SectorFlow[];
  etfFlows: EtfFlow[];
  macroStatus: MacroItem[];
  btcTreasuries: BtcTreasury[];
  vcActivity: VcActivity[];
  aiBriefing: string[];
  newsHeadlines: NewsHeadline[];
  isLoading: boolean;
  isError: boolean;
  isConnected: boolean;
  lastUpdated: Date | null;
  refresh: () => void;
}

export function useDashboardData(wallet?: string): DashboardData {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [stats, setStats] = useState<SignalStats>({ today: 0, thisWeek: 0, accuracy: 0 });
  const [market, setMarket] = useState<MarketStatus | null>(null);
  const [sectorFlows, setSectorFlows] = useState<SectorFlow[]>([]);
  const [etfFlows, setEtfFlows] = useState<EtfFlow[]>([]);
  const [macroStatus, setMacroStatus] = useState<MacroItem[]>([]);
  const [btcTreasuries, setBtcTreasuries] = useState<BtcTreasury[]>([]);
  const [vcActivity, setVcActivity] = useState<VcActivity[]>([]);
  const [aiBriefing, setAiBriefing] = useState<string[]>([]);
  const [newsHeadlines, setNewsHeadlines] = useState<NewsHeadline[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
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

      setSignals(sigData.signals ?? []);
      setStats(sigData.stats ?? { today: 0, thisWeek: 0, accuracy: 0 });
      setMarket(mktData.market ?? null);
      setSectorFlows(secData.sectorFlows ?? []);
      setEtfFlows(etfData.etfFlows ?? []);
      setMacroStatus(macData.macroStatus ?? []);
      setBtcTreasuries(btcData.btcTreasuries ?? []);
      setVcActivity(vcData.vcActivity ?? []);
      setAiBriefing(newsData.aiBriefing ?? []);
      setNewsHeadlines(newsData.newsHeadlines ?? []);
      setLastUpdated(new Date());
    } catch {
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Load data immediately via REST so the page never hangs waiting for SSE
    fetchAll();
    let pollId: ReturnType<typeof setInterval> | null = setInterval(fetchAll, REFRESH_INTERVAL_MS);
    const sseUrl = wallet
      ? `${API_BASE}/api/stream?wallet=${encodeURIComponent(wallet)}`
      : `${API_BASE}/api/stream`;
    const es = new EventSource(sseUrl);

    es.addEventListener('access_denied', () => {
      // Server rejected wallet as free tier — close SSE, stay on polling fallback
      es.close();
      setIsConnected(false);
    });

    es.onmessage = (e) => {
      // SSE connected — cancel REST polling, SSE keeps data fresh
      if (pollId !== null) {
        clearInterval(pollId);
        pollId = null;
      }
      let snap: Record<string, unknown>;
      try {
        snap = JSON.parse(e.data);
      } catch {
        return;
      }
      if (snap.signals) setSignals(snap.signals as Signal[]);
      if (snap.stats) setStats(snap.stats as SignalStats);
      if (snap.market) setMarket(snap.market as MarketStatus);
      if (snap.sectorFlows) setSectorFlows(snap.sectorFlows as SectorFlow[]);
      if (snap.etfFlows) setEtfFlows(snap.etfFlows as EtfFlow[]);
      if (snap.macroStatus) setMacroStatus(snap.macroStatus as MacroItem[]);
      if (snap.btcTreasuries) setBtcTreasuries(snap.btcTreasuries as BtcTreasury[]);
      if (snap.vcActivity) setVcActivity(snap.vcActivity as VcActivity[]);
      if (snap.aiBriefing) setAiBriefing(snap.aiBriefing as string[]);
      if (snap.newsHeadlines) setNewsHeadlines(snap.newsHeadlines as NewsHeadline[]);
      setLastUpdated(new Date());
      setIsConnected(true);
      setIsLoading(false);
      setIsError(false);
    };

    es.onerror = () => {
      setIsConnected(false);
      // SSE failed — polling fallback is already running, nothing to do
    };

    return () => {
      es.close();
      if (pollId !== null) clearInterval(pollId);
    };
  }, [fetchAll, wallet]);

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
    isConnected,
    lastUpdated,
    refresh: fetchAll,
  };
}
