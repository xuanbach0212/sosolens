import type { NewsHeadline } from "@/types";
import { Warn } from "@/components/icons";

interface Props {
  briefing: string[];
  news: NewsHeadline[];
  lastUpdated: Date | null;
}

function formatTimestamp(d: Date): string {
  const h = String(d.getUTCHours()).padStart(2, '0');
  const m = String(d.getUTCMinutes()).padStart(2, '0');
  const s = String(d.getUTCSeconds()).padStart(2, '0');
  return `${h}:${m}:${s} UTC`;
}

export default function BottomBar({ briefing, news, lastUpdated }: Props) {
  return (
    <div
      className="border-t border-terminal-border bg-terminal-panel px-3 py-2 flex gap-6 overflow-hidden"
      style={{ gridColumn: "1 / -1" }}
    >
      {/* AI Briefing */}
      <div className="flex-1 min-w-0">
        <div className="text-[10px] font-bold text-terminal-muted tracking-widest mb-1">
          AI BRIEFING{lastUpdated ? ` · ${formatTimestamp(lastUpdated)}` : ""}
        </div>
        <div className="space-y-0.5">
          {briefing.length === 0 ? (
            <div className="text-[10px] text-terminal-muted italic">AI briefing generating...</div>
          ) : (
            briefing.map((point, i) => (
              <div
                key={i}
                className="text-[10px] text-terminal-text whitespace-nowrap overflow-hidden text-ellipsis"
                title={point}
              >
                <span className="text-terminal-green mr-1">{i + 1}.</span>
                {point}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Divider */}
      <div className="border-l border-terminal-border" />

      {/* News */}
      <div className="flex-1 min-w-0">
        <div className="text-[10px] font-bold text-terminal-muted tracking-widest mb-1">NEWS</div>
        <div className="space-y-0.5">
          {news.length === 0 && (
            <div className="text-[10px] text-terminal-muted italic">Loading headlines...</div>
          )}
          {news.map((item, i) => (
            <div key={i} className="text-[10px] text-terminal-text flex items-start gap-1 truncate">
              <span className="text-terminal-muted shrink-0">•</span>
              <span className="truncate">
                {item.text}{" "}
                <span className="text-terminal-muted">— {item.source}</span>
                {item.macroSensitive && (
                  <span className="ml-1 inline-flex"><Warn /></span>
                )}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
