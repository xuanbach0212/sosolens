/* global React */
// SoSoLens terminal — all panels. Treatments (palette/type/glyph/border) are driven
// by classes on the root; indicator glyph-vs-emoji comes through ThemeCtx.

const { createContext, useContext, useState, useEffect, useRef } = React;
const ThemeCtx = createContext({ glyph: false });

/* ---------- indicator helpers ---------- */
function VerdictMark({ type }) {
  const { glyph } = useContext(ThemeCtx);
  if (!glyph) {
    const e = type === 'BUY' ? '🟢' : type === 'WATCH' ? '🟡' : '🔴';
    return <span className="vmark">{e}</span>;
  }
  const g = type === 'BUY' ? '▲' : type === 'WATCH' ? '◆' : '▼';
  const cls = type === 'BUY' ? 'up' : type === 'WATCH' ? 'warn' : 'down';
  return <span className={`vmark gl ${cls}`}>{g}</span>;
}

function Dot({ signal }) {
  const { glyph } = useContext(ThemeCtx);
  if (!glyph) return <span>{signal}</span>;
  const map = { '🟢': 'up', '🟡': 'warn', '🔴': 'down', '⚪': 'mut' };
  return <span className={`gl ${map[signal] || 'mut'}`}>●</span>;
}

function Check({ ok }) {
  const { glyph } = useContext(ThemeCtx);
  if (!glyph) return <span>{ok ? '✅' : '❌'}</span>;
  return <span className={`gl ${ok ? 'up' : 'down'}`}>{ok ? '✓' : '✗'}</span>;
}

function Warn() {
  const { glyph } = useContext(ThemeCtx);
  return glyph ? <span className="gl warn">▲</span> : <span>⚠️</span>;
}

/* ---------- tiny charts ---------- */
function Sparkline({ data, up }) {
  if (!data || data.length < 2) return null;
  const w = 52, h = 16;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const step = Math.max(1, Math.ceil(data.length / 60));
  const pts = data.filter((_, i) => i % step === 0);
  const points = pts
    .map((v, i) => `${(i / (pts.length - 1)) * w},${h - ((v - min) / range) * h}`)
    .join(' ');
  return (
    <svg className={`spark ${up ? 'up' : 'down'}`} width={w} height={h}>
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

function EtfBarChart({ data, width = 120, height = 14 }) {
  if (!data || data.length === 0) return null;
  const BUCKETS = 7;
  const bs = Math.ceil(data.length / BUCKETS);
  const buckets = [];
  for (let i = 0; i < data.length; i += bs) {
    const slice = data.slice(i, i + bs);
    buckets.push(slice.reduce((s, v) => s + v, 0) / slice.length);
  }
  const maxAbs = Math.max(...buckets.map((v) => Math.abs(v)), 1);
  const gap = 2;
  const barW = (width - gap * (buckets.length - 1)) / buckets.length;
  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      {buckets.map((v, i) => {
        const barH = Math.max(2, (Math.abs(v) / maxAbs) * (height - 2));
        return (
          <rect key={i} x={i * (barW + gap)} y={height - barH}
            width={Math.max(1, barW)} height={barH}
            className={v >= 0 ? 'barUp' : 'barDown'} />
        );
      })}
    </svg>
  );
}

/* ---------- live value flash ---------- */
function Flash({ value, children }) {
  const prev = useRef(value);
  const [dir, setDir] = useState('');
  useEffect(() => {
    if (value > prev.current) setDir('up');
    else if (value < prev.current) setDir('down');
    prev.current = value;
    const id = setTimeout(() => setDir(''), 700);
    return () => clearTimeout(id);
  }, [value]);
  return <span className={`flash ${dir}`}>{children}</span>;
}

/* ---------- crawling ticker tape ---------- */
const fmtTape = (p) =>
  p < 1 ? '$' + p.toFixed(p < 0.001 ? 7 : 4)
        : '$' + p.toLocaleString('en-US', { maximumFractionDigits: 2 });

function TickerTape({ items }) {
  const row = items.map((x, i) => (
    <span className="tapeitem" key={i}>
      <span className="tapesym">{x.sym}</span>
      <span className="mut">{fmtTape(x.price)}</span>
      <span className={x.pct >= 0 ? 'up' : 'down'}>{x.pct >= 0 ? '▲' : '▼'} {Math.abs(x.pct).toFixed(1)}%</span>
    </span>
  ));
  return (
    <div className="tape">
      <div className="tapelabel">TAPE</div>
      <div className="tapeview"><div className="tapetrack">{row}{row}</div></div>
    </div>
  );
}

/* ---------- TOP BAR ---------- */
function TopBar({ market, live, riskEnvironment, clock }) {
  const { glyph } = useContext(ThemeCtx);
  const btcHist = live.btcHist, ethHist = live.ethHist;
  const btcPct = (btcHist[btcHist.length - 1] / btcHist[0] - 1) * 100;
  const ethPct = (ethHist[ethHist.length - 1] / ethHist[0] - 1) * 100;
  const mcapPct = (live.mcap / 3.71 - 1) * 100 + 1.8;
  const volPct = (live.vol / 142 - 1) * 100 + 6.2;
  const usd0 = (n) => '$' + Math.round(n).toLocaleString('en-US');
  const pct = (p) => (p >= 0 ? '+' : '') + p.toFixed(1) + '%';
  const regime = riskEnvironment === 'risk-off'
    ? { label: 'RISK-OFF', cls: 'down' }
    : riskEnvironment === 'risk-on'
    ? { label: 'RISK-ON', cls: 'up' }
    : { label: 'NEUTRAL', cls: 'warn' };
  const fg = Math.round(live.fg);
  const fgCls = fg <= 24 ? 'down' : fg <= 55 ? 'warn' : 'up';
  const fgLabel = fg <= 24 ? 'EXTREME FEAR' : fg <= 44 ? 'FEAR' : fg <= 55 ? 'NEUTRAL' : fg <= 74 ? 'GREED' : 'EXTREME GREED';
  const clockStr = clock.toLocaleTimeString('en-US', { hour12: false, timeZone: 'UTC' });
  return (
    <header className="topbar">
      <span className="brand">SOSOLENS <span className="blink up">●</span><span className="brandlive">LIVE</span></span>
      <span className="sep">│</span>
      <span className="tk">MARKET <span className={market.sentimentPositive ? 'up' : 'down'}>
        {glyph ? <span className="gl up">●</span> : (market.sentimentPositive ? '🟢' : '🔴')} {market.sentiment}</span></span>
      <span className="sep">│</span>
      <span className="tk">MACRO <span className={regime.cls}>{regime.label}{regime.cls === 'down' && !glyph ? ' ⚠' : ''}</span></span>
      <span className="sep">│</span>
      <span className="tk">BTC <b><Flash value={Math.round(live.btc)}>{usd0(live.btc)}</Flash></b> <span className={btcPct >= 0 ? 'up' : 'down'}>{pct(btcPct)}</span><Sparkline data={btcHist} up={btcPct >= 0} /></span>
      <span className="sep">│</span>
      <span className="tk">ETH <b><Flash value={Math.round(live.eth)}>{usd0(live.eth)}</Flash></b> <span className={ethPct >= 0 ? 'up' : 'down'}>{pct(ethPct)}</span><Sparkline data={ethHist} up={ethPct >= 0} /></span>
      <span className="sep">│</span>
      <span className="tk">MCAP <b><Flash value={Math.round(live.mcap * 1000)}>${live.mcap.toFixed(2)}T</Flash></b> <span className={mcapPct >= 0 ? 'up' : 'down'}>{pct(mcapPct)}</span></span>
      <span className="sep">│</span>
      <span className="tk">VOL <b><Flash value={Math.round(live.vol)}>${Math.round(live.vol)}B</Flash></b> <span className={volPct >= 0 ? 'up' : 'down'}>{pct(volPct)}</span></span>
      <span className="sep">│</span>
      <span className="tk">F/G <Flash value={fg}><span className={fgCls}>{fg}</span></Flash> <span className="mut">{fgLabel}</span></span>
      <span className="status">
        <span className="up"><span className="blink">●</span> SSE LIVE · {clockStr} UTC</span>
        <span className="sep">│</span>
        <span className="wallet">0x7a3f…b21c <span className="badge-pro">PRO</span></span>
      </span>
    </header>
  );
}

/* ---------- SIGNAL FEED ---------- */
const OUT_CLS = { WIN: 'oWin', LOSS: 'oLoss', SKIP: 'oSkip', PENDING: 'oPend' };

function SignalFeed({ signals, selectedId, onSelect, stats, outcomes }) {
  return (
    <aside className="feed">
      <div className="panelhdr"><span className="plabel">SIGNALS</span></div>
      <div className="feedlist">
        {signals.map((s) => {
          const active = s.id === selectedId;
          return (
            <button key={s.id} onClick={() => onSelect(s.id)}
              className={`feedrow ${active ? 'active' : ''} ${s.isNew ? 'isnew' : ''} v-${s.type}`}>
              <div className={`feedtype t-${s.type}`}><VerdictMark type={s.type} /> {s.type}</div>
              <div className="feedsector">{s.sector}</div>
              <div className="feedmeta">{s.confidence}% · {s.risk} · {s.timeAgo}</div>
            </button>
          );
        })}
      </div>
      <div className="trail">
        <div className="tinylabel">OUTCOME TRAIL · 48H</div>
        <div className="trailgrid">
          {outcomes.slice(-36).map((o, i) => (
            <div key={i} className={`tcell ${OUT_CLS[o.outcome]}`}
              title={`${o.signalType} · ${o.outcome}`} />
          ))}
        </div>
      </div>
      <div className="statbox">
        <div className="statrow"><span>TODAY</span><b>{stats.today} sig</b></div>
        <div className="statrow"><span>THIS WEEK</span><b>{stats.thisWeek}</b></div>
        <div className="statrow"><span>ACCURACY</span><b className="up">{stats.accuracy}%</b></div>
      </div>
    </aside>
  );
}

/* ---------- SIGNAL DETAIL ---------- */
function SectionHeader({ title }) {
  return (
    <div className="secthdr"><span className="plabel">{title}</span><div className="rule" /></div>
  );
}

/* ---------- numeric parse/format helpers (for live ticking) ---------- */
function parseNum(s) {
  return parseFloat(String(s).replace(/−/g, '-').replace(/[^0-9.\-]/g, '')) || 0;
}
function fmtTokenPrice(n) {
  if (n >= 1000) return '$' + Math.round(n).toLocaleString('en-US');
  if (n >= 1) return '$' + n.toFixed(2);
  if (n >= 0.001) return '$' + n.toFixed(4);
  return '$' + n.toFixed(7);
}
function fmtFlowM(v) {
  return (v >= 0 ? '+' : '−') + '$' + Math.round(Math.abs(v)) + 'M';
}
function arrowsFor(v) {
  return v >= 0 ? (Math.abs(v) > 150 ? '↑↑' : '↑') : '↓';
}

function SignalDetail({ signal, tick, agentRun, live }) {
  const [tokens, setTokens] = useState(() => seedTokens(signal.topTokens));
  const [dsFlash, setDsFlash] = useState(false);

  useEffect(() => { setTokens(seedTokens(signal.topTokens)); }, [signal.id]);

  const firstTick = useRef(true);
  useEffect(() => {
    if (firstTick.current) { firstTick.current = false; return; }
    if (!live) return;
    setTokens((ts) => ts.map((t) => t.has ? {
      ...t,
      price: t.price * (1 + (Math.random() - 0.5) * 0.01),
      pct: +(t.pct + (Math.random() - 0.5) * 0.4).toFixed(1),
    } : t));
  }, [tick]);

  useEffect(() => {
    if (!live || agentRun === 0) return;
    setDsFlash(true);
    const id = setTimeout(() => setDsFlash(false), 1000);
    return () => clearTimeout(id);
  }, [agentRun]);

  return (
    <section className="detail">
      <div className="detailscroll">
        <div className="vhead">
          <div className={`verdict t-${signal.type}`}>
            <VerdictMark type={signal.type} /> {signal.type} SIGNAL — {signal.sector.toUpperCase()}
          </div>
          <div className="confrow">
            <div className="confwrap">
              <div className="conftrack">
                <div className={`conffill b-${signal.type}`} style={{ width: `${signal.confidence}%` }} />
              </div>
              <div className="confnum">CONFIDENCE {signal.confidence}%</div>
            </div>
            <span className={`riskbadge r-${signal.risk}`}>{signal.risk} RISK</span>
          </div>
        </div>

        <div>
          <SectionHeader title="ANALYSIS" />
          <p className="analysis">{signal.explanation}</p>
        </div>

        <div>
          <SectionHeader title="DATA SOURCES" />
          <table className="dtable">
            <thead>
              <tr><th>SOURCE</th><th className="r">VALUE</th><th className="r">SIGNAL</th></tr>
            </thead>
            <tbody>
              {signal.dataSources.map((row) => (
                <tr key={row.name}>
                  <td className="mut">{row.name}</td>
                  <td className={`r ${dsFlash ? 'flash sync' : ''}`}><b>{row.value}</b></td>
                  <td className="r"><Dot signal={row.signal} /> {row.arrow || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {tokens.length > 0 && (
          <div>
            <SectionHeader title="TOP TOKENS IN SECTOR" />
            <div className="tokengrid">
              {tokens.map((t) => (
                <div key={t.symbol} className="token box">
                  <div className="tsym">{t.symbol}</div>
                  {t.has && (
                    <>
                      <div className="tprice mut">
                        {live ? <Flash value={Math.round(t.price * 1e4)}>{fmtTokenPrice(t.price)}</Flash> : fmtTokenPrice(t.price)}
                      </div>
                      <div className={t.pct >= 0 ? 'up' : 'down'}>{t.pct >= 0 ? '+' : ''}{t.pct.toFixed(1)}%</div>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <SectionHeader title="SIMILAR PAST SIGNALS" />
          <table className="dtable">
            <tbody>
              {signal.pastSignals.map((p, i) => (
                <tr key={i}>
                  <td className="mut">{p.date}</td>
                  <td>{p.label}</td>
                  <td className={p.success ? 'up' : 'down'}>{p.result}</td>
                  <td className="r"><Check ok={p.success} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="acc mut">Signal accuracy: <span className="up">{signal.accuracy}%</span></div>
        </div>

        {signal.sodexPair && signal.sodexPair !== '—' && (
          <div className="sodex box">
            <div className="sodexhdr warn"><SodexMark /> Trade on SoDEX</div>
            <div className="sodexpair">{signal.sodexPair}</div>
            <div className="mut sodexmeta">Slippage {signal.sodexSlippage} · Est. {signal.sodexEstOutput}</div>
            <button className="sodexbtn">[ OPEN SODEX ]</button>
          </div>
        )}
      </div>
    </section>
  );
}

function seedTokens(arr) {
  return arr.map((t) => ({
    symbol: t.symbol,
    has: !!(t.price && t.price !== '—'),
    price: parseNum(t.price),
    pct: parseNum(t.change),
  }));
}

function SodexMark() {
  const { glyph } = useContext(ThemeCtx);
  return glyph ? <span className="gl warn">▸</span> : <span>⚡</span>;
}

/* ---------- MARKET INTELLIGENCE ---------- */
const MAX_FLOW = 28;
function PanelHeader({ title }) {
  return <div className="secthdr"><span className="plabel">{title}</span><div className="rule" /></div>;
}

function MarketIntelligence({ sectorFlows, etfFlows, macroStatus, btcTreasuries, vcActivity, etfHistory, tick, agentRun, live }) {
  const [sectors, setSectors] = useState(() => sectorFlows.map((s) => ({ ...s })));
  const [etfs, setEtfs] = useState(() => etfFlows.map((e) => ({ name: e.name, total: !!e.total, val: parseNum(e.flow) })));
  const [bars, setBars] = useState(() => ({
    BTC: etfHistory.map((s) => s.btcFlow).slice(-14),
    ETH: etfHistory.map((s) => s.ethFlow).slice(-14),
  }));
  const [synced, setSynced] = useState(false);
  const first = useRef(true);

  useEffect(() => {
    if (first.current) { first.current = false; return; }
    if (!live) return;
    setSectors((ss) => ss.map((s) => ({ ...s, change: +(s.change + (Math.random() - 0.5) * 0.6).toFixed(1) })));
    setEtfs((es) => {
      const next = es.map((e) => e.total ? e : { ...e, val: e.val * (1 + (Math.random() - 0.5) * 0.03) });
      const sum = next.filter((e) => !e.total).reduce((a, e) => a + e.val, 0);
      const total = next.find((e) => e.total);
      if (total) total.val = sum;
      return next;
    });
    setBars((b) => ({
      BTC: [...b.BTC.slice(-13), b.BTC[b.BTC.length - 1] * (1 + (Math.random() - 0.5) * 0.25)],
      ETH: [...b.ETH.slice(-13), b.ETH[b.ETH.length - 1] * (1 + (Math.random() - 0.5) * 0.3)],
    }));
  }, [tick]);

  useEffect(() => {
    if (!live || agentRun === 0) return;
    setSynced(true);
    const id = setTimeout(() => setSynced(false), 1200);
    return () => clearTimeout(id);
  }, [agentRun]);

  return (
    <aside className="intel">
      <div className="intelgroup">
        <PanelHeader title="SECTOR FLOWS · 7D" />
        <div className="sectorgrid">
          {sectors.map((s) => {
            const intensity = Math.min(Math.abs(s.change) / MAX_FLOW, 1);
            const alpha = (0.14 + intensity * 0.6).toFixed(2);
            const pos = s.change > 0;
            const bg = pos
              ? `color-mix(in oklab, var(--green) ${Math.round(alpha * 100)}%, transparent)`
              : s.change < 0
              ? `color-mix(in oklab, var(--red) ${Math.round(alpha * 100)}%, transparent)`
              : 'rgba(255,255,255,0.04)';
            return (
              <div key={s.name} className="scell" style={{ backgroundColor: bg }}>
                <span className="sname">{s.name}</span>
                <span className={`sval ${pos ? 'up' : s.change < 0 ? 'down' : 'mut'}`}>
                  {live ? <Flash value={Math.round(s.change * 10)}>{pos ? '+' : ''}{s.change}%</Flash> : <>{pos ? '+' : ''}{s.change}%</>}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="intelgroup">
        <PanelHeader title="ETF FLOWS · 7D" />
        <div className="etflist">
          {etfs.map((e) => (
            <div key={e.name}>
              <div className={`etfrow ${e.total ? 'etftotal' : ''}`}>
                <span className="mut">{e.name}</span>
                <span className={e.val >= 0 ? 'up' : 'down'}>
                  {live ? <Flash value={Math.round(e.val)}>{fmtFlowM(e.val)} {arrowsFor(e.val)}</Flash> : <>{fmtFlowM(e.val)} {arrowsFor(e.val)}</>}
                </span>
              </div>
              {!e.total && (
                <div className="etfbar">
                  <EtfBarChart data={e.name === 'BTC ETF' ? bars.BTC : bars.ETH} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className={`intelgroup ${synced ? 'synced' : ''}`}>
        <PanelHeader title="MACRO STATUS" />
        <div className="kvlist">
          {macroStatus.map((m) => (
            <div key={m.name} className="kvrow">
              <span className="mut">{m.name}</span>
              <span className={m.warning ? 'warn' : ''}>{m.value} {m.arrow}</span>
            </div>
          ))}
        </div>
      </div>

      <div className={`intelgroup ${synced ? 'synced' : ''}`}>
        <PanelHeader title="BTC TREASURIES" />
        <div className="kvlist">
          {btcTreasuries.map((t) => (
            <div key={t.company} className="treas">
              <div className="tcompany">{t.company}</div>
              <div className="kvrow">
                <span className="mut">{t.btcHeld}</span>
                <span className={t.positive === true ? 'up' : t.positive === false ? 'down' : 'mut'}>
                  {t.weeklyChange} {t.positive === true ? '↑' : t.positive === false ? '↓' : '·'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className={`intelgroup ${synced ? 'synced' : ''}`}>
        <PanelHeader title="VC ACTIVITY · 7D" />
        <div className="kvlist">
          {vcActivity.map((v) => (
            <div key={v.sector} className="kvrow">
              <span className="mut">{v.sector}</span>
              <span>{v.rounds} round{v.rounds !== 1 ? 's' : ''} <span className="up">{v.totalUsd}</span></span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}

/* ---------- BOTTOM BAR ---------- */
function BottomBar({ briefing, news, briefingKey, stamp }) {
  return (
    <footer className="bottombar">
      <div className="bbcol">
        <div className="tinylabel">AI BRIEFING · {stamp}</div>
        <div className="bblist fadein" key={briefingKey}>
          {briefing.map((p, i) => (
            <div key={i} className="bbitem"><span className="up bbnum">{i + 1}.</span>{p}</div>
          ))}
        </div>
      </div>
      <div className="bbdivider" />
      <div className="bbcol">
        <div className="tinylabel">NEWS</div>
        <div className="bblist">
          {news.map((n, i) => (
            <div key={n.id || i} className={`bbitem ${n.isNew ? 'newsin' : ''}`}><span className="mut bbdot">•</span>
              <span className="bbnews">{n.text} <span className="mut">— {n.source}</span>{n.macroSensitive && <> <Warn /></>}</span>
            </div>
          ))}
        </div>
      </div>
    </footer>
  );
}

Object.assign(window, {
  ThemeCtx, TopBar, SignalFeed, SignalDetail, MarketIntelligence, BottomBar, TickerTape,
});
