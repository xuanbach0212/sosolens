/* global React, ReactDOM, DATA, ThemeCtx, TopBar, SignalFeed, SignalDetail, MarketIntelligence, BottomBar, TickerTape, useTweaks, TweaksPanel, TweakSection, TweakRadio, TweakToggle */
const { useState, useEffect, useRef } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "preset": "refined",
  "palette": "warm",
  "type": "scaled",
  "indicators": "glyph",
  "borders": "calm",
  "live": true,
  "tempo": "calm"
}/*EDITMODE-END*/;

const PRESETS = {
  current: { palette: 'neon', type: 'flat', indicators: 'emoji', borders: 'boxed' },
  refined: { palette: 'warm', type: 'scaled', indicators: 'glyph', borders: 'calm' },
};

const TAPE_SEED = [
  { sym: 'BTC', price: 101240, pct: 2.1 }, { sym: 'ETH', price: 3184, pct: 1.4 },
  { sym: 'SOL', price: 168.4, pct: 3.2 }, { sym: 'TAO', price: 412.8, pct: 9.2 },
  { sym: 'FET', price: 1.34, pct: 6.7 }, { sym: 'ARB', price: 0.84, pct: 5.3 },
  { sym: 'OP', price: 1.92, pct: 4.0 }, { sym: 'ONDO', price: 1.12, pct: 2.4 },
  { sym: 'LDO', price: 1.41, pct: 3.2 }, { sym: 'RNDR', price: 7.91, pct: 4.1 },
  { sym: 'HNT', price: 6.41, pct: 1.9 }, { sym: 'WIF', price: 1.88, pct: -12.3 },
  { sym: 'PEPE', price: 0.0000091, pct: -9.7 }, { sym: 'MKR', price: 1840, pct: 1.1 },
  { sym: 'AKT', price: 3.22, pct: 11.4 }, { sym: 'AR', price: 8.77, pct: 0.4 },
];

// new signals reuse existing detail shapes so the detail panel stays valid
const NEW_SIGNAL_POOL = [
  { ...DATA.signals[3], sector: 'Bitcoin L2', type: 'WATCH', confidence: 64, risk: 'MEDIUM' },
  { ...DATA.signals[0], sector: 'AI Agents', type: 'BUY', confidence: 84, risk: 'MEDIUM' },
  { ...DATA.signals[2], sector: 'Gaming', type: 'AVOID', confidence: 73, risk: 'HIGH' },
  { ...DATA.signals[5], sector: 'Liquid Staking', type: 'BUY', confidence: 70, risk: 'LOW' },
  { ...DATA.signals[1], sector: 'RWA', type: 'WATCH', confidence: 60, risk: 'LOW' },
];

// AI briefing rotates on each agent run beat
const BRIEFING_POOL = [
  DATA.aiBriefing,
  [
    'ETF inflows extend to a 10th session (+$358M net); rotation breadth widening beyond AI into L2 + staking.',
    'DXY slips below 103 and 10Y real yield eases — duration-sensitive crypto basket catching a bid.',
    'Funding still benign on majors; leverage not yet crowded outside memecoins — constructive tape.',
  ],
  [
    'AI-Agents momentum cooling slightly (+15% / 7d) as profit-taking emerges; BUY thesis intact, trim chase risk.',
    'New DePIN + RWA rounds lift primary-market activity to a 6-week high — watch for secondary follow-through.',
    'Macro calendar quiet until next CPI; agent holds RISK-ON, no regime-change triggers armed.',
  ],
];

// fresh headlines rotate into the news feed
const NEWS_POOL = [
  { text: 'ETH ETF options approval reportedly nears final SEC sign-off', source: 'Reg Desk', macroSensitive: false },
  { text: 'Stablecoin supply hits new ATH, +$4.2B this week — liquidity tailwind', source: 'On-chain', macroSensitive: false },
  { text: 'Fed speakers strike dovish tone ahead of next FOMC', source: 'Macro', macroSensitive: true },
  { text: 'L2 sequencer revenue up 31% MoM as activity rotates onchain', source: 'SoSoValue', macroSensitive: false },
  { text: 'Tier-1 fund opens $300M crypto-AI thesis vehicle', source: 'VC Desk', macroSensitive: false },
  { text: 'BTC dominance ticks down as alt rotation accelerates', source: 'On-chain', macroSensitive: false },
];

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [selectedId, setSelectedId] = useState(DATA.signals[0].id);
  const [signals, setSignals] = useState(DATA.signals);
  const [stats, setStats] = useState(DATA.stats);
  const [outcomes, setOutcomes] = useState(DATA.signalOutcomes);
  const [tape, setTape] = useState(TAPE_SEED);
  const [clock, setClock] = useState(() => new Date());
  const [tick, setTick] = useState(0);
  const [agentRun, setAgentRun] = useState(0);
  const [briefingIdx, setBriefingIdx] = useState(0);
  const [news, setNews] = useState(() => DATA.newsHeadlines.map((n, i) => ({ ...n, id: 'seed-' + i })));
  const [live, setLive] = useState(() => ({
    btc: 101240, eth: 3184, mcap: 3.71, vol: 142, fg: 72,
    btcHist: DATA.priceHistory.map((p) => p.btcPrice).slice(-60),
    ethHist: DATA.priceHistory.map((p) => p.ethPrice).slice(-60),
  }));

  const signal = signals.find((s) => s.id === selectedId) || signals[0];

  // live clock (always ticks)
  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  // price + tape tick
  useEffect(() => {
    if (!t.live) return;
    const ms = t.tempo === 'active' ? 1100 : 2100;
    const id = setInterval(() => {
      setLive((L) => {
        const j = (v, vol) => v * (1 + (Math.random() - 0.5) * vol);
        const btc = j(L.btc, 0.0018), eth = j(L.eth, 0.0022);
        return {
          btc, eth,
          mcap: +j(L.mcap, 0.0016).toFixed(3),
          vol: Math.max(80, j(L.vol, 0.012)),
          fg: Math.max(2, Math.min(98, L.fg + (Math.random() - 0.5) * 1.6)),
          btcHist: [...L.btcHist.slice(-59), btc],
          ethHist: [...L.ethHist.slice(-59), eth],
        };
      });
      setTape((T) => T.map((x) => ({
        ...x,
        price: x.price * (1 + (Math.random() - 0.5) * 0.012),
        pct: +(x.pct + (Math.random() - 0.5) * 0.4).toFixed(1),
      })));
      setTick((n) => n + 1);
    }, ms);
    return () => clearInterval(id);
  }, [t.live, t.tempo]);

  // new signal injection
  useEffect(() => {
    if (!t.live) return;
    const ms = t.tempo === 'active' ? 8000 : 15000;
    const id = setInterval(() => {
      const tpl = NEW_SIGNAL_POOL[Math.floor(Math.random() * NEW_SIGNAL_POOL.length)];
      const sig = { ...tpl, id: 'live-' + Date.now(), timeAgo: 'just now', isNew: true };
      setSignals((s) => [sig, ...s].slice(0, 8));
      setStats((st) => ({ ...st, today: st.today + 1, thisWeek: st.thisWeek + 1 }));
      setOutcomes((o) => [...o, {
        detectorId: 'd0', signalType: sig.type, outcome: 'PENDING',
        recordedAt: new Date().toISOString(),
      }].slice(-60));
      setTimeout(() => setSignals((s) => s.map((x) => x.id === sig.id ? { ...x, isNew: false } : x)), 1700);
    }, ms);
    return () => clearInterval(id);
  }, [t.live, t.tempo]);

  // news beat — a fresh headline slides in
  useEffect(() => {
    if (!t.live) return;
    const ms = t.tempo === 'active' ? 15000 : 30000;
    const id = setInterval(() => {
      const pick = NEWS_POOL[Math.floor(Math.random() * NEWS_POOL.length)];
      const item = { ...pick, id: 'news-' + Date.now(), isNew: true };
      setNews((ns) => [item, ...ns].slice(0, 4));
      setTimeout(() => setNews((ns) => ns.map((n) => n.id === item.id ? { ...n, isNew: false } : n)), 1600);
    }, ms);
    return () => clearInterval(id);
  }, [t.live, t.tempo]);

  // agent-run beat — briefing re-fades, data sources refresh, fundamentals sync
  useEffect(() => {
    if (!t.live) return;
    const ms = t.tempo === 'active' ? 30000 : 60000;
    const id = setInterval(() => {
      setAgentRun((n) => n + 1);
      setBriefingIdx((i) => (i + 1) % BRIEFING_POOL.length);
    }, ms);
    return () => clearInterval(id);
  }, [t.live, t.tempo]);

  const applyPreset = (p) => setTweak({ preset: p, ...PRESETS[p] });
  const rootCls = `pal-${t.palette} type-${t.type} ind-${t.indicators} bd-${t.borders}`;

  return (
    <ThemeCtx.Provider value={{ glyph: t.indicators === 'glyph' }}>
      <div className={`terminal ${rootCls} ${t.live ? '' : 'paused'}`}>
        <TopBar market={DATA.market} live={live} riskEnvironment={DATA.riskEnvironment} clock={clock} />
        <TickerTape items={tape} />
        <SignalFeed signals={signals} selectedId={selectedId} onSelect={setSelectedId} stats={stats} outcomes={outcomes} />
        <SignalDetail signal={signal} tick={tick} agentRun={agentRun} live={t.live} />
        <MarketIntelligence
          sectorFlows={DATA.sectorFlows} etfFlows={DATA.etfFlows} macroStatus={DATA.macroStatus}
          btcTreasuries={DATA.btcTreasuries} vcActivity={DATA.vcActivity} etfHistory={DATA.etfHistory}
          tick={tick} agentRun={agentRun} live={t.live} />
        <BottomBar
          briefing={BRIEFING_POOL[briefingIdx]} news={news} briefingKey={briefingIdx}
          stamp={clock.toLocaleTimeString('en-US', { hour12: false, timeZone: 'UTC' }) + ' UTC'} />
      </div>

      <TweaksPanel title="Design pass">
        <TweakSection label="Preset" />
        <TweakRadio label="Compare" value={t.preset} options={['current', 'refined']} onChange={applyPreset} />
        <TweakSection label="Motion" />
        <TweakToggle label="Live data" value={t.live} onChange={(v) => setTweak('live', v)} />
        <TweakRadio label="Tempo" value={t.tempo} options={['calm', 'active']} onChange={(v) => setTweak('tempo', v)} />
        <TweakSection label="Mix & match" />
        <TweakRadio label="Palette" value={t.palette} options={['neon', 'warm']} onChange={(v) => setTweak({ palette: v, preset: 'custom' })} />
        <TweakRadio label="Type" value={t.type} options={['flat', 'scaled']} onChange={(v) => setTweak({ type: v, preset: 'custom' })} />
        <TweakRadio label="Indicators" value={t.indicators} options={['emoji', 'glyph']} onChange={(v) => setTweak({ indicators: v, preset: 'custom' })} />
        <TweakRadio label="Borders" value={t.borders} options={['boxed', 'calm']} onChange={(v) => setTweak({ borders: v, preset: 'custom' })} />
      </TweaksPanel>
    </ThemeCtx.Provider>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
