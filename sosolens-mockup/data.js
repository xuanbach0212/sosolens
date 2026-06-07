// Sample data for the SoSoLens terminal mockup — shapes mirror frontend/types/index.ts
(function () {
  // deterministic-ish price history for sparklines
  function walk(start, n, vol, drift) {
    const out = [];
    let v = start;
    for (let i = 0; i < n; i++) {
      const seed = Math.sin(i * 12.9898 + start) * 43758.5453;
      const r = seed - Math.floor(seed) - 0.5;
      v = v * (1 + drift + r * vol);
      out.push(v);
    }
    return out;
  }

  const btcSeries = walk(101200, 60, 0.012, 0.0011);
  const ethSeries = walk(3120, 60, 0.014, 0.0008);

  const priceHistory = btcSeries.map((b, i) => ({
    timestamp: new Date(Date.now() - (60 - i) * 36e5).toISOString(),
    btcPrice: b,
    ethPrice: ethSeries[i],
  }));

  const etfHistory = Array.from({ length: 21 }, (_, i) => {
    const s = Math.sin(i * 0.7) ;
    return {
      timestamp: new Date(Date.now() - (21 - i) * 36e5).toISOString(),
      btcFlow: Math.round((s * 220 + 140) ),
      ethFlow: Math.round((Math.cos(i * 0.6) * 90 + 30)),
      totalFlow: 0,
    };
  });

  const signals = [
    {
      id: 'sig-1',
      type: 'BUY',
      sector: 'AI Agents',
      confidence: 87,
      risk: 'MEDIUM',
      timeAgo: '4m ago',
      explanation:
        'ETF net inflows into the AI-adjacent basket spiked +312% vs the trailing 7-day mean while sector capital rotation turned net-positive for the first time in nine sessions. Spot volume confirms the move rather than fading it, and the macro regime flipped risk-on after the softer-than-expected CPI print. Confluence of flow, rotation, and macro favors accumulation; size moderately given elevated realized vol.',
      dataSources: [
        { name: 'ETF net flow (24h)', value: '+$312M', signal: '🟢', arrow: '↑' },
        { name: 'Sector rotation (7d)', value: '+18.4%', signal: '🟢', arrow: '↑' },
        { name: 'Spot volume z-score', value: '+2.3σ', signal: '🟢', arrow: '↑' },
        { name: 'Funding rate', value: '0.021%', signal: '🟡', arrow: '→' },
        { name: 'Macro regime', value: 'RISK-ON', signal: '🟢', arrow: '↑' },
      ],
      topTokens: [
        { symbol: 'TAO', price: '$412.80', change: '+9.2%', positive: true },
        { symbol: 'FET', price: '$1.34', change: '+6.7%', positive: true },
        { symbol: 'RNDR', price: '$7.91', change: '+4.1%', positive: true },
        { symbol: 'AKT', price: '$3.22', change: '+11.4%', positive: true },
        { symbol: 'AGIX', price: '$0.58', change: '+5.0%', positive: true },
        { symbol: 'GRT', price: '$0.19', change: '−1.2%', positive: false },
      ],
      pastSignals: [
        { date: 'May 28', label: 'BUY · AI Agents', result: '+14.2% / 72h', success: true },
        { date: 'May 14', label: 'BUY · AI Agents', result: '+8.1% / 48h', success: true },
        { date: 'Apr 30', label: 'WATCH · AI Agents', result: '−3.4% / 72h', success: false },
      ],
      accuracy: 74,
      sodexPair: 'BUY TAO/USDC',
      sodexSlippage: '0.30%',
      sodexEstOutput: '≈ 2.41 TAO',
    },
    {
      id: 'sig-2',
      type: 'WATCH',
      sector: 'RWA',
      confidence: 61,
      risk: 'LOW',
      timeAgo: '22m ago',
      explanation:
        'Tokenized-treasury TVL continues to grind higher but flow momentum is decelerating and rotation is only marginally positive. No anomaly trigger fired; this is a trend-continuation watch, not an entry. Re-evaluate if 24h ETF flow crosses +$120M or rotation breaks +6%.',
      dataSources: [
        { name: 'Tokenized TVL (7d)', value: '+$1.9B', signal: '🟢', arrow: '↑' },
        { name: 'Sector rotation (7d)', value: '+3.1%', signal: '🟡', arrow: '→' },
        { name: 'Flow momentum', value: 'Decel.', signal: '🟡', arrow: '↓' },
        { name: 'Macro regime', value: 'RISK-ON', signal: '🟢', arrow: '↑' },
      ],
      topTokens: [
        { symbol: 'ONDO', price: '$1.12', change: '+2.4%', positive: true },
        { symbol: 'MKR', price: '$1,840', change: '+1.1%', positive: true },
        { symbol: 'PENDLE', price: '$4.66', change: '−0.8%', positive: false },
      ],
      pastSignals: [
        { date: 'May 21', label: 'WATCH · RWA', result: '+5.9% / 96h', success: true },
        { date: 'May 02', label: 'BUY · RWA', result: '+12.0% / 72h', success: true },
      ],
      accuracy: 68,
      sodexPair: '—',
      sodexSlippage: '',
      sodexEstOutput: '—',
    },
    {
      id: 'sig-3',
      type: 'AVOID',
      sector: 'Memecoins',
      confidence: 79,
      risk: 'HIGH',
      timeAgo: '38m ago',
      explanation:
        'Capital is rotating out of the memecoin basket at −24% over 7 days while funding stays richly positive — a classic late-stage long-crowding setup. ETF and institutional flow give zero support to this sector. Avoid fresh longs; existing positions should tighten risk.',
      dataSources: [
        { name: 'Sector rotation (7d)', value: '−24.1%', signal: '🔴', arrow: '↓' },
        { name: 'Funding rate', value: '0.087%', signal: '🔴', arrow: '↑' },
        { name: 'Spot volume z-score', value: '−1.4σ', signal: '🔴', arrow: '↓' },
        { name: 'Long/short ratio', value: '2.8', signal: '🔴', arrow: '↑' },
      ],
      topTokens: [
        { symbol: 'WIF', price: '$1.88', change: '−12.3%', positive: false },
        { symbol: 'PEPE', price: '$0.0000091', change: '−9.7%', positive: false },
        { symbol: 'BONK', price: '$0.0000183', change: '−7.1%', positive: false },
      ],
      pastSignals: [
        { date: 'May 19', label: 'AVOID · Memecoins', result: '−18.6% avoided', success: true },
        { date: 'May 06', label: 'AVOID · Memecoins', result: '−9.2% avoided', success: true },
      ],
      accuracy: 81,
      sodexPair: '—',
      sodexSlippage: '',
      sodexEstOutput: '—',
    },
    {
      id: 'sig-4',
      type: 'BUY',
      sector: 'L2 Scaling',
      confidence: 71,
      risk: 'MEDIUM',
      timeAgo: '1h ago',
      explanation:
        'Rollup activity and ETF flow both inflect positive as the macro regime turns supportive. Rotation into L2s is early but accelerating. Moderate-conviction accumulation; scale in rather than chase.',
      dataSources: [
        { name: 'ETF net flow (24h)', value: '+$96M', signal: '🟢', arrow: '↑' },
        { name: 'Sector rotation (7d)', value: '+9.7%', signal: '🟢', arrow: '↑' },
        { name: 'Active addresses', value: '+14%', signal: '🟢', arrow: '↑' },
        { name: 'Funding rate', value: '0.014%', signal: '🟡', arrow: '→' },
      ],
      topTokens: [
        { symbol: 'ARB', price: '$0.84', change: '+5.3%', positive: true },
        { symbol: 'OP', price: '$1.92', change: '+4.0%', positive: true },
        { symbol: 'STRK', price: '$0.46', change: '+2.1%', positive: true },
      ],
      pastSignals: [
        { date: 'May 24', label: 'BUY · L2 Scaling', result: '+7.7% / 72h', success: true },
        { date: 'May 10', label: 'WATCH · L2 Scaling', result: '+1.2% / 48h', success: false },
      ],
      accuracy: 66,
      sodexPair: 'BUY ARB/USDC',
      sodexSlippage: '0.25%',
      sodexEstOutput: '≈ 1,190 ARB',
    },
    {
      id: 'sig-5',
      type: 'WATCH',
      sector: 'DePIN',
      confidence: 58,
      risk: 'MEDIUM',
      timeAgo: '2h ago',
      explanation:
        'VC funding into DePIN remains the strongest of any sector this week but secondary-market flow has not yet followed. Primary/secondary divergence keeps this a watch until spot volume confirms.',
      dataSources: [
        { name: 'VC funding (7d)', value: '$284M', signal: '🟢', arrow: '↑' },
        { name: 'Sector rotation (7d)', value: '+1.8%', signal: '🟡', arrow: '→' },
        { name: 'Spot volume z-score', value: '+0.4σ', signal: '🟡', arrow: '→' },
      ],
      topTokens: [
        { symbol: 'HNT', price: '$6.41', change: '+1.9%', positive: true },
        { symbol: 'IOTX', price: '$0.041', change: '−0.6%', positive: false },
        { symbol: 'AR', price: '$8.77', change: '+0.4%', positive: true },
      ],
      pastSignals: [
        { date: 'May 16', label: 'WATCH · DePIN', result: '+4.3% / 96h', success: true },
      ],
      accuracy: 63,
      sodexPair: '—',
      sodexSlippage: '',
      sodexEstOutput: '—',
    },
    {
      id: 'sig-6',
      type: 'BUY',
      sector: 'Liquid Staking',
      confidence: 69,
      risk: 'LOW',
      timeAgo: '3h ago',
      explanation:
        'Staking inflows and ETH ETF demand reinforce each other as the macro regime turns risk-on. Low-volatility accumulation candidate with favorable risk/reward.',
      dataSources: [
        { name: 'ETH ETF flow (24h)', value: '+$54M', signal: '🟢', arrow: '↑' },
        { name: 'Staking inflow (7d)', value: '+220K ETH', signal: '🟢', arrow: '↑' },
        { name: 'Sector rotation (7d)', value: '+6.2%', signal: '🟢', arrow: '↑' },
      ],
      topTokens: [
        { symbol: 'LDO', price: '$1.41', change: '+3.2%', positive: true },
        { symbol: 'RPL', price: '$9.88', change: '+2.0%', positive: true },
        { symbol: 'SSV', price: '$12.10', change: '+1.4%', positive: true },
      ],
      pastSignals: [
        { date: 'May 22', label: 'BUY · Liquid Staking', result: '+6.0% / 96h', success: true },
        { date: 'May 08', label: 'BUY · Liquid Staking', result: '+4.4% / 72h', success: true },
      ],
      accuracy: 77,
      sodexPair: 'BUY LDO/USDC',
      sodexSlippage: '0.20%',
      sodexEstOutput: '≈ 709 LDO',
    },
  ];

  const stats = { today: 6, thisWeek: 41, accuracy: 73 };

  const market = {
    sentiment: 'BULLISH',
    sentimentPositive: true,
    btcPrice: '$101,240',
    btcChange: '+2.1%',
    ethPrice: '$3,184',
    ethChange: '+1.4%',
    mcap: '$3.71T',
    mcapChange: '+1.8%',
    vol: '$142B',
    volChange: '+6.2%',
    fearGreed: 72,
    fearGreedLabel: 'GREED',
  };

  const sectorFlows = [
    { name: 'AI Agents', change: 18 },
    { name: 'L2 Scaling', change: 10 },
    { name: 'Liquid Stk', change: 6 },
    { name: 'RWA', change: 3 },
    { name: 'DePIN', change: 2 },
    { name: 'Bitcoin L2', change: -4 },
    { name: 'Gaming', change: -9 },
    { name: 'DeFi', change: -12 },
    { name: 'Memecoins', change: -24 },
  ];

  const etfFlows = [
    { name: 'BTC ETF', flow: '+$312M', arrows: '↑↑', positive: true },
    { name: 'ETH ETF', flow: '+$54M', arrows: '↑', positive: true },
    { name: 'SOL ETF', flow: '−$8M', arrows: '↓', positive: false },
    { name: 'NET 24H', flow: '+$358M', arrows: '↑', positive: true, total: true },
  ];

  const macroStatus = [
    { name: 'Fed funds', value: '4.25%', arrow: '→' },
    { name: 'CPI (YoY)', value: '2.7%', arrow: '↓' },
    { name: 'DXY', value: '103.4', arrow: '↓' },
    { name: '10Y yield', value: '4.18%', arrow: '↑', warning: true },
    { name: 'M2 (YoY)', value: '+3.1%', arrow: '↑' },
  ];

  const btcTreasuries = [
    { company: 'MicroStrategy', btcHeld: '601,550 BTC', weeklyChange: '+5,400', positive: true },
    { company: 'Marathon Digital', btcHeld: '34,794 BTC', weeklyChange: '+210', positive: true },
    { company: 'Tesla', btcHeld: '11,509 BTC', weeklyChange: '0', positive: null },
    { company: 'Block, Inc.', btcHeld: '8,485 BTC', weeklyChange: '−120', positive: false },
  ];

  const vcActivity = [
    { sector: 'DePIN', rounds: 7, totalUsd: '$284M' },
    { sector: 'AI Agents', rounds: 5, totalUsd: '$197M' },
    { sector: 'RWA', rounds: 4, totalUsd: '$156M' },
    { sector: 'L2 Scaling', rounds: 3, totalUsd: '$88M' },
    { sector: 'Gaming', rounds: 2, totalUsd: '$41M' },
  ];

  const aiBriefing = [
    'AI-Agents basket leads rotation (+18% / 7d) as ETF inflows spike +312% — strongest BUY confluence on the board.',
    'Macro flipped risk-on post-CPI (2.7% YoY); softening DXY and falling 10Y real-yield support duration assets.',
    'Memecoins bleeding capital (−24% / 7d) with crowded longs — agent flags AVOID, tighten risk on existing exposure.',
  ];

  const newsHeadlines = [
    { text: 'Spot BTC ETFs log 9th straight day of net inflows, +$312M', source: 'SoSoValue', macroSensitive: false },
    { text: 'CPI prints 2.7% YoY, below 2.9% consensus — rate-cut odds rise', source: 'Macro', macroSensitive: true },
    { text: 'Two new DePIN rounds close $120M combined, led by tier-1 funds', source: 'VC Desk', macroSensitive: false },
  ];

  const signalOutcomes = (() => {
    const seq = ['WIN','WIN','LOSS','WIN','SKIP','WIN','WIN','LOSS','WIN','WIN','PENDING','WIN','SKIP','LOSS','WIN','WIN','WIN','PENDING','WIN','LOSS','WIN','WIN','SKIP','WIN','WIN','LOSS','WIN','PENDING'];
    const types = ['BUY','WATCH','AVOID','BUY','WATCH'];
    return seq.map((o, i) => ({
      detectorId: 'd' + (i % 3),
      signalType: types[i % types.length],
      outcome: o,
      recordedAt: new Date(Date.now() - (seq.length - i) * 17e5).toISOString(),
    }));
  })();

  window.DATA = {
    signals, stats, market, sectorFlows, etfFlows, macroStatus,
    btcTreasuries, vcActivity, aiBriefing, newsHeadlines,
    priceHistory, etfHistory, signalOutcomes,
    riskEnvironment: 'risk-on',
    lastUpdated: new Date(),
  };
})();
