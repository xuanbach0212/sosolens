import type { Signal, SignalType } from "@/types";

const TYPE_COLOR: Record<SignalType, string> = {
  BUY: "text-terminal-green",
  WATCH: "text-terminal-yellow",
  AVOID: "text-terminal-red",
};

const TYPE_BAR_COLOR: Record<SignalType, string> = {
  BUY: "bg-terminal-green",
  WATCH: "bg-terminal-yellow",
  AVOID: "bg-terminal-red",
};

const RISK_COLOR: Record<string, string> = {
  LOW: "text-terminal-green border-terminal-green",
  MEDIUM: "text-terminal-yellow border-terminal-yellow",
  HIGH: "text-terminal-red border-terminal-red",
};

interface Props {
  signal: Signal;
}

function SectionHeader({ title }: { title: string }) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <span className="text-[10px] font-bold text-terminal-muted tracking-widest">{title}</span>
      <div className="flex-1 border-t border-terminal-border" />
    </div>
  );
}

export default function SignalDetail({ signal }: Props) {
  const typeColor = TYPE_COLOR[signal.type];
  const barColor = TYPE_BAR_COLOR[signal.type];

  return (
    <div
      className="border-r border-terminal-border flex flex-col overflow-hidden"
      style={{ gridColumn: "2", gridRow: "2" }}
    >
      <div className="overflow-y-auto flex-1 px-4 py-3 space-y-4">
        {/* Header */}
        <div>
          <div className={`text-sm font-bold ${typeColor}`}>
            {signal.type === "BUY" ? "🟢" : signal.type === "WATCH" ? "🟡" : "🔴"}{" "}
            {signal.type} SIGNAL — {signal.sector.toUpperCase()}
          </div>
          <div className="flex items-center gap-3 mt-2">
            <div className="flex-1">
              <div className="h-2 bg-terminal-border rounded-sm overflow-hidden">
                <div
                  className={`h-full rounded-sm ${barColor}`}
                  style={{ width: `${signal.confidence}%` }}
                />
              </div>
              <div className="text-[10px] text-terminal-muted mt-0.5">
                Confidence {signal.confidence}%
              </div>
            </div>
            <span
              className={`text-[10px] border px-1.5 py-0.5 rounded ${RISK_COLOR[signal.risk]}`}
            >
              {signal.risk} RISK
            </span>
          </div>
        </div>

        {/* Explanation */}
        <div>
          <SectionHeader title="ANALYSIS" />
          <p className="text-xs text-terminal-text leading-relaxed">{signal.explanation}</p>
        </div>

        {/* Data Sources */}
        <div>
          <SectionHeader title="DATA SOURCES" />
          <table className="w-full text-[10px]">
            <thead>
              <tr className="text-terminal-muted border-b border-terminal-border">
                <th className="text-left pb-1 font-normal">SOURCE</th>
                <th className="text-right pb-1 font-normal">VALUE</th>
                <th className="text-right pb-1 font-normal">SIGNAL</th>
              </tr>
            </thead>
            <tbody>
              {signal.dataSources.map((row) => (
                <tr key={row.name} className="border-b border-terminal-border">
                  <td className="py-1 text-terminal-muted">{row.name}</td>
                  <td className="py-1 text-right text-terminal-text">{row.value}</td>
                  <td className="py-1 text-right">
                    {row.signal} {row.arrow ?? ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Top Tokens */}
        <div>
          <SectionHeader title="TOP TOKENS IN SECTOR" />
          <div className="grid grid-cols-3 gap-1">
            {signal.topTokens.map((token) => (
              <div key={token.symbol} className="bg-terminal-panel border border-terminal-border rounded px-2 py-1">
                <div className="text-[10px] font-bold text-terminal-text">{token.symbol}</div>
                <div className="text-[10px] text-terminal-muted">{token.price}</div>
                <div
                  className={`text-[10px] ${
                    token.positive ? "text-terminal-green" : "text-terminal-red"
                  }`}
                >
                  {token.change}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Past Signals */}
        <div>
          <SectionHeader title="SIMILAR PAST SIGNALS" />
          <table className="w-full text-[10px]">
            <tbody>
              {signal.pastSignals.map((past, i) => (
                <tr key={i} className="border-b border-terminal-border">
                  <td className="py-1 text-terminal-muted">{past.date}</td>
                  <td className="py-1 text-terminal-text">{past.label}</td>
                  <td
                    className={`py-1 ${
                      past.success ? "text-terminal-green" : "text-terminal-red"
                    }`}
                  >
                    {past.result}
                  </td>
                  <td className="py-1 text-right">{past.success ? "✅" : "❌"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="text-[10px] text-terminal-muted mt-1">
            Signal accuracy:{" "}
            <span className={signal.accuracy >= 70 ? "text-terminal-green" : "text-terminal-yellow"}>
              {signal.accuracy}%
            </span>
          </div>
        </div>

        {/* SoDEX Trade Button */}
        <div>
          <div className="border border-terminal-border rounded p-3 bg-terminal-panel">
            <div className="text-[10px] font-bold text-terminal-yellow mb-2">⚡ Trade on SoDEX</div>
            <div className="text-[10px] text-terminal-text mb-0.5">{signal.sodexPair}</div>
            <div className="text-[10px] text-terminal-muted mb-0.5">
              Slippage {signal.sodexSlippage}
            </div>
            <div className="text-[10px] text-terminal-muted mb-3">
              Est. output: {signal.sodexEstOutput}
            </div>
            <button className="w-full border border-terminal-yellow text-terminal-yellow text-[10px] py-1.5 rounded hover:bg-terminal-yellow hover:text-terminal-bg transition-colors tracking-widest font-bold">
              [ OPEN SODEX ]
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
