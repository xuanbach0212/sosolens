# Terminal UI Design

**Style**: Bloomberg Terminal — one screen, always visible, no navigation, maximum information density.

---

## Layout Structure

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ SOSOALPHA ●LIVE │ MARKET: 🟢 RISK-ON │ BTC $98,420 +2.1% │ ETH $3,210 +1.8%     │
│                 │ MCAP: $3.42T +1.9% │ VOL: $124B  +12%  │ FEAR/GREED: 72 GREED  │
├─────────────────┬─────────────────────────────────────────┬───────────────────────┤
│ SIGNALS         │ SIGNAL DETAIL (center, main panel)      │ MARKET INTELLIGENCE   │
│  (left col)     │                                         │  (right col)          │
│                 │                                         │                       │
│ Signal feed     │ Selected signal:                        │ Sector flows heatmap  │
│ (scrollable)    │  - Confidence bar                       │ ETF flows (24h)       │
│                 │  - Plain-English explanation             │ Macro status          │
│ Signal stats    │  - Data sources table (with values)     │ BTC treasuries        │
│  (bottom left)  │  - Top tokens in sector + prices        │ VC activity           │
│                 │  - Historical accuracy                   │                       │
│                 │  - SoDEX trade button                   │                       │
├─────────────────┴─────────────────────────────────────────┴───────────────────────┤
│ AI BRIEFING (3 bullet points) + NEWS HEADLINES (3 items)                          │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## Full Wireframe

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ SOSOALPHA ●LIVE │ MARKET: 🟢 RISK-ON │ BTC $98,420 +2.1% │ ETH $3,210 +1.8%     │
│                 │ MCAP: $3.42T +1.9% │ VOL: $124B  +12%  │ FEAR/GREED: 72 GREED  │
├─────────────────┬─────────────────────────────────────────┬───────────────────────┤
│ SIGNALS         │ 🟢 AI SECTOR — BUY SIGNAL               │ SECTOR FLOWS (7D)     │
│ ─────────────── │ ──────────────────────────────────────  │ ───────────────────── │
│ 🟢 BUY          │ Confidence ████████░░ 80%  Risk: MEDIUM  │ AI/ML  ████████ +40% │
│  AI Sector      │                                         │ DeFi   ██████   +27% │
│  80% · MED · 2h │ ETF inflows into AI tokens spiked 40%   │ RWA    █████    +18% │
│                 │ this week while price hasn't reacted.   │ L1     ████      +8% │
│ 🟡 WATCH        │ Historically, price follows inflows in  │ BTC    ███       +5% │
│  DeFi Sector    │ 3–5 days. BTC treasuries stable →       │ Stables██        +1% │
│  65% · LOW · 5h │ macro not bearish. No negative news.    │ L2     ░░        -5% │
│                 │                                         │ Gaming ░░░      -14% │
│ 🔴 AVOID        │ DATA SOURCES              VALUE  SIGNAL  │ NFT    ░░░░     -22% │
│  Layer 2        │ ETF Net Inflow (7d)     +$240M   🟢 ↑↑  │                      │
│  85% · HIGH · 1d│ Sector Capital Flow      Inflow   🟢 ↑  │ ETF FLOWS (24H)      │
│                 │ Macro Environment        Risk-On  🟢     │ ───────────────────── │
│ 🟡 WATCH        │ News Sentiment           Neutral  ⚪     │ BTC ETF  +$380M  ↑↑↑ │
│  BTC            │ BTC Treasuries           Stable   ⚪     │ ETH ETF  +$120M  ↑↑  │
│  55% · LOW · 2d │ VC Fundraising           2 rounds 🟡     │ SOL ETF   +$42M  ↑   │
│                 │ Price vs Flow Gap        Large    🟢 ↑↑  │ Other     +$28M  ↑   │
│ 🟡 WATCH        │                                         │ TOTAL    +$570M  ↑↑↑ │
│  RWA Sector     │ TOP TOKENS IN SECTOR                    │                      │
│  60% · LOW · 3d │ FET   $2.41 +3.2%  NEAR  $7.82 +1.1%  │ MACRO STATUS         │
│                 │ RNDR  $8.12 +4.5%  TAO  $412.0 +2.8%  │ ───────────────────── │
│ ─────────────── │ AGIX  $1.23 +2.1%  FLock  $0.84 +1.9% │ Fed Rate   5.25%  →  │
│ TODAY    3 sig  │                                         │ US CPI     3.2%   ↓  │
│ THIS WEEK 14    │ SIMILAR PAST SIGNALS                    │ DXY        104.2  ↓  │
│ ACCURACY  71%   │ Feb 14 AI BUY → +18% over 5d  ✅       │ 10Y Yield  4.31%  ↑  │
│                 │ Mar 02 AI BUY → +12% over 4d  ✅       │ M2 Supply  ↑ expand  │
│                 │ Apr 11 AI BUY →  -3% over 5d  ❌       │ FOMC     in 7d  ⚠️   │
│                 │ Signal accuracy: 2/3 (67%)              │ CPI      in 12d      │
│                 │                                         │                      │
│                 │ ┌─────────────────────────────────────┐ │ BTC TREASURIES       │
│                 │ │ ⚡ Trade on SoDEX                   │ │ ───────────────────── │
│                 │ │ BUY FET/USDC  ·  slippage 1%        │ │ MicroStrategy        │
│                 │ │ Est. output: 41.5 FET per $100      │ │  214,246 BTC +1,282↑ │
│                 │ │              [ OPEN SODEX ]          │ │ Marathon             │
│                 │ └─────────────────────────────────────┘ │  40,435 BTC  ±0   ⚪ │
│                 │                                         │ Tesla                │
│                 │                                         │  11,509 BTC  ±0   ⚪ │
│                 │                                         │                      │
│                 │                                         │ VC ACTIVITY (7D)     │
│                 │                                         │ ───────────────────── │
│                 │                                         │ DeFi  3 rounds  $48M │
│                 │                                         │ AI    2 rounds  $31M │
│                 │                                         │ RWA   1 round   $15M │
├─────────────────┴─────────────────────────────────────────┴───────────────────────┤
│ AI BRIEFING · May 4 · 14:32 UTC                                                   │
│ 1. ETF inflows hit 2-month high ($570M). Last time this happened BTC +12% in 5d  │
│ 2. Fed minutes tonight 18:00 UTC — AI sector drops avg 8% if hawkish. De-risk    │
│ 3. DeFi VC: 3 new rounds this week signals smart money rotating from L2 → DeFi   │
│                                                                                   │
│ NEWS  • BlackRock BTC ETF records $380M single-day inflow — Bloomberg             │
│       • Paradigm leads $31M raise in AI infra protocol — The Block               │
│       • Fed officials signal patience on rate cuts — Reuters  ⚠️ macro-sensitive  │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## Panel Breakdown

### Top Bar
- Live status indicator
- Market sentiment (Risk-On / Risk-Off / Neutral)
- BTC and ETH price + 24h change
- Total market cap + 24h change
- Total 24h volume + change
- Fear & Greed index

**APIs**: Currencies market-snapshot, Macro API

---

### Left Column — Signal Feed

**Signal cards** (each shows):
- Signal type: 🟢 BUY / 🟡 WATCH / 🔴 AVOID
- Sector or asset name
- Confidence % · Risk level · Time ago

**Signal stats** (bottom of left column):
- Signals generated today
- Signals this week
- Overall accuracy %

**Interaction**: click any card → center panel updates

---

### Center Panel — Signal Detail

- Signal type + sector header
- Confidence progress bar + risk level badge
- Plain-English explanation (3–4 lines, written by AI)
- **Data Sources Table**: each API module used, its current value, and directional signal (🟢/🟡/🔴/⚪)
- **Top tokens in sector**: up to 6 tokens with current price + 24h change
- **Historical signal accuracy**: last 3 similar signals with outcome and accuracy rate
- **SoDEX trade button**: pre-filled pair, slippage, estimated output per $100

---

### Right Column — Market Intelligence

**Sector Flows (7D)**
- Bar chart for each major sector (9 sectors shown)
- Color: green = inflow, red = outflow
- Percentage change label

**ETF Flows (24H)**
- BTC ETF, ETH ETF, SOL ETF, Other
- Dollar inflow/outflow with direction arrows
- Total row

**Macro Status**
- Fed Rate, US CPI, DXY, 10Y Yield, M2 Supply
- Each with current value and trend arrow (→ ↑ ↓)
- Next macro event with days-until countdown + ⚠️ if high-impact

**BTC Treasuries**
- Top 3 companies: name, BTC held, weekly change + arrow

**VC Activity (7D)**
- Top 3 sectors with round count and total USD raised

---

### Bottom Bar — AI Briefing + News

**AI Briefing** (3 numbered points):
- Each is one sentence, actionable
- Generated fresh every hour from all SoSoValue data

**News** (3 headlines):
- Title · Source
- ⚠️ flag if macro-sensitive

---

## Design Principles

- **Dark theme only** — terminal aesthetic, green/yellow/red on dark background
- **No navigation** — everything visible at once, click signal to update center
- **Data density** — every pixel has a purpose, no whitespace wasted
- **Color is signal** — green = positive/inflow, red = negative/outflow, yellow = neutral/watch, white = data
- **Numbers first** — actual values always shown, not just up/down arrows
- **SoSoValue branding** — every data point credits SoSoValue as source

---

## Tech Stack for Frontend

- **Framework**: Next.js (App Router)
- **Styling**: Tailwind CSS with dark theme config
- **Font**: JetBrains Mono or IBM Plex Mono (terminal feel)
- **State**: React state for selected signal, polling for live data
- **Data refresh**: every 60 seconds for prices, every 3600s for AI signals
- **Layout**: CSS Grid — fixed columns, no responsive breakpoints needed (desktop only)
