export type SignalType = 'BUY' | 'SELL' | 'WATCH' | 'AVOID';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface DataSourceRow {
  name: string;
  value: string;
  signal: '🟢' | '🟡' | '🔴' | '⚪';
  arrow?: string;
}

export interface Token {
  symbol: string;
  price: string;
  change: string;
  positive: boolean;
}

export interface PastSignal {
  date: string;
  label: string;
  result: string;
  success: boolean;
}

export interface Signal {
  id: string;
  type: SignalType;
  sector: string;
  confidence: number;
  risk: RiskLevel;
  timeAgo: string;
  explanation: string;
  dataSources: DataSourceRow[];
  topTokens: Token[];
  pastSignals: PastSignal[];
  accuracy: number;
  sodexPair: string;
  sodexSlippage: string;
  sodexEstOutput: string;
}

export interface SignalStats {
  today: number;
  thisWeek: number;
  accuracy: number;
}

export interface MarketStatus {
  sentiment: string;
  sentimentPositive: boolean;
  btcPrice: string;
  btcChange: string;
  ethPrice: string;
  ethChange: string;
  mcap: string;
  mcapChange: string;
  vol: string;
  volChange: string;
  fearGreed: number;
  fearGreedLabel: string;
}

export interface SectorFlow {
  name: string;
  change: number;
}

export interface EtfFlow {
  name: string;
  flow: string;
  arrows: string;
  positive: boolean;
  total?: boolean;
}

export interface MacroItem {
  name: string;
  value: string;
  arrow: string;
  warning?: boolean;
}

export interface BtcTreasury {
  company: string;
  btcHeld: string;
  weeklyChange: string;
  positive: boolean | null;
}

export interface VcActivity {
  sector: string;
  rounds: number;
  totalUsd: string;
}

export interface NewsHeadline {
  text: string;
  source: string;
  macroSensitive?: boolean;
}

export interface PriceSnapshot {
  timestamp: string;
  btcPrice: number;
  ethPrice: number;
}

export interface SignalOutcomeBlock {
  detectorId: string;
  signalType: SignalType;
  outcome: 'WIN' | 'LOSS' | 'SKIP' | 'PENDING';
  recordedAt: string;
}

export interface EtfFlowSnapshot {
  timestamp: string;
  btcFlow: number;
  ethFlow: number;
  totalFlow: number;
}
