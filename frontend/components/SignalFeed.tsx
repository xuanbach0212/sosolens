'use client';

import type { Signal, SignalType } from "@/types";

const TYPE_COLOR: Record<SignalType, string> = {
  BUY: "text-terminal-green border-terminal-green",
  SELL: "text-terminal-red border-terminal-red",
  WATCH: "text-terminal-yellow border-terminal-yellow",
  AVOID: "text-terminal-red border-terminal-red",
};

const TYPE_EMOJI: Record<SignalType, string> = {
  BUY: "🟢",
  SELL: "🔴",
  WATCH: "🟡",
  AVOID: "🔴",
};

interface Props {
  signals: Signal[];
  selectedId: string;
  onSelect: (id: string) => void;
  stats: { today: number; thisWeek: number; accuracy: number };
  isLoading: boolean;
}

export default function SignalFeed({ signals, selectedId, onSelect, stats, isLoading }: Props) {
  return (
    <div
      className="border-r border-terminal-border flex flex-col overflow-hidden"
      style={{ gridColumn: "1", gridRow: "2" }}
    >
      <div className="px-3 py-2 border-b border-terminal-border">
        <span className="text-xs font-bold text-terminal-muted tracking-widest">SIGNALS</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading && signals.length === 0 ? (
          <div className="px-3 py-4 text-[10px] text-terminal-muted italic tracking-widest animate-pulse">
            CONNECTING...
          </div>
        ) : signals.length === 0 ? (
          <div className="px-3 py-4 text-[10px] text-terminal-muted italic leading-relaxed">
            AGENT RUNNING<br />
            First signals in ~60s
          </div>
        ) : (
          signals.map((signal) => {
            const isActive = signal.id === selectedId;
            const colorClass = TYPE_COLOR[signal.type];
            return (
              <button
                key={signal.id}
                onClick={() => onSelect(signal.id)}
                className={`w-full text-left px-3 py-2 border-b border-terminal-border border-l-2 cursor-pointer transition-colors ${
                  isActive
                    ? `border-l-current bg-terminal-panel ${colorClass}`
                    : "border-l-transparent hover:bg-terminal-panel"
                }`}
              >
                <div className={`text-xs font-bold ${colorClass.split(" ")[0]}`}>
                  {TYPE_EMOJI[signal.type]} {signal.type}
                </div>
                <div className="text-[11px] text-terminal-text mt-0.5">{signal.sector}</div>
                <div className="text-[10px] text-terminal-muted mt-0.5">
                  {signal.confidence}% · {signal.risk} · {signal.timeAgo}
                </div>
              </button>
            );
          })
        )}
      </div>

      <div className="px-3 py-2 border-t border-terminal-border bg-terminal-panel text-[10px] text-terminal-muted space-y-0.5">
        <div className="flex justify-between">
          <span>TODAY</span>
          <span className="text-terminal-text">{stats.today} sig</span>
        </div>
        <div className="flex justify-between">
          <span>THIS WEEK</span>
          <span className="text-terminal-text">{stats.thisWeek}</span>
        </div>
        <div className="flex justify-between">
          <span>ACCURACY</span>
          <span className={stats.accuracy > 0 ? "text-terminal-green" : "text-terminal-muted"}>
            {stats.accuracy > 0 ? `${stats.accuracy}%` : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}
