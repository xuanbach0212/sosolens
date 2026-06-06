type Verdict = "BUY" | "WATCH" | "AVOID" | "SELL";
export type DotVariant = "up" | "warn" | "down" | "mut";

const DOT_COLOR: Record<DotVariant, string> = {
  up: "text-terminal-green",
  warn: "text-terminal-yellow",
  down: "text-terminal-red",
  mut: "text-terminal-muted",
};

// Backend detector payload uses emoji strings for the data-sources signal field
// (legacy contract from the wave 1 detectors). Translate to variant once, at the
// edge — callers never reference the emoji literal directly.
export function dotVariantFromSignal(signal: string): DotVariant {
  if (signal === "\u{1F7E2}") return "up";   // green circle
  if (signal === "\u{1F7E1}") return "warn"; // yellow circle
  if (signal === "\u{1F534}") return "down"; // red circle
  return "mut";
}

export function VerdictMark({ type }: { type: Verdict }) {
  const g = type === "BUY" ? "▲" : type === "WATCH" ? "◆" : "▼";
  const cls =
    type === "BUY"
      ? "text-terminal-green"
      : type === "WATCH"
        ? "text-terminal-yellow"
        : "text-terminal-red";
  return <span className={`text-[0.9em] ${cls}`}>{g}</span>;
}

export function Dot({ variant }: { variant: DotVariant }) {
  return <span className={`text-[0.92em] ${DOT_COLOR[variant]}`}>●</span>;
}

export function Check({ ok }: { ok: boolean }) {
  return (
    <span className={ok ? "text-terminal-green" : "text-terminal-red"}>
      {ok ? "✓" : "✗"}
    </span>
  );
}

export function Warn() {
  return <span className="text-terminal-yellow">▲</span>;
}

export function Bolt() {
  return <span className="text-terminal-yellow">▸</span>;
}
