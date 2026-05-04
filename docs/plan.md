# Project Plan

## What We're Building

**AI Signal Platform** — a one-screen, Bloomberg-terminal-style dashboard that watches SoSoValue's data 24/7 and surfaces actionable trading signals with plain-English explanations.

Think: Bloomberg Terminal meets AI analyst. One screen, dense information, everything visible at once.

## The Problem It Solves

Retail crypto users have access to price charts but not institutional-grade data (ETF flows, BTC treasury accumulation, sector capital rotation, macro indicators). SoSoValue has this data. We turn it into signals anyone can act on — with one click to execute on SoDEX.

## Contest Fit

| Criteria | How We Score |
|----------|-------------|
| User Value (30%) | Retail users get institutional-grade signals with reasoning |
| Working Demo (25%) | Live dashboard with real SoSoValue data — show in 90 seconds |
| Logic/Workflow (20%) | Clear: data → AI → signal → explanation → action |
| API Integration (15%) | All relevant SoSoValue modules used |
| UX (10%) | One-screen, information-dense, Bloomberg-style |

## Hackathon Requirements

**Required:**
- ✅ SoSoValue API integration (multiple modules)
- ✅ Clear use case: retail users discover opportunities
- ✅ Complete flow: data in → signal out → trade
- ✅ Demo: live dashboard with verifiable data

**Bonus (we hit all of these):**
- ✅ SoDEX API integration (trade button)
- ✅ AI-enhanced functionality (signal generation + explanation)
- ✅ Opportunity discovery, signal generation, market explanation
- ✅ Risk controls (confidence score, risk level per signal)
- ✅ Complete insight-to-action flow
- ✅ Better product experience (one-screen terminal UX)

## SoSoValue Integration

| API Module | How We Use It |
|-----------|--------------|
| Sector / Index API | Detect capital flow rotation between sectors |
| ETF API | Institutional money movement signals |
| BTC Treasuries API | Corporate accumulation tracking |
| Macro API | Risk-on / risk-off environment |
| Feeds API | News sentiment per token/sector |
| Fundraising API | Smart money (VC) entry signals |
| Currency & Pairs | Price context for signals |

## Architecture

```
SoSoValue APIs (7 modules)
        │
        ▼
AI Agent (runs every hour on server)
  - fetches all data
  - detects anomalies / patterns
  - generates signal + plain-English explanation
  - assigns confidence + risk level
        │
        ▼
Backend (stores signals, serves to frontend)
        │
        ▼
One-screen Terminal Dashboard (Next.js)
  - Signal feed panel
  - Signal detail + data panel
  - Sector flow heatmap panel
  - Macro status panel
  - Daily briefing panel
  - SoDEX trade button
```

## One-Person Business Model

- Free tier: delayed signals (24h lag)
- Premium: real-time signals — pay X USDC/month via smart contract
- Operator earns all subscription revenue

## What We Build

- [ ] SoSoValue API integration layer (all 7 modules)
- [ ] AI signal generation agent (Python)
- [ ] Signal storage backend (simple API)
- [ ] One-screen terminal frontend (Next.js)
- [ ] SoDEX trade button integration
- [ ] On-chain subscription contract (simple ERC-20 paywall)

## What We Don't Build

- ❌ Copy trading execution
- ❌ Vault / fund contracts
- ❌ SSI Protocol integration
- ❌ Portfolio tracking per user
- ❌ Mobile app
- ❌ Social features
- ❌ Multiple pages / complex navigation

## Milestones

- [x] Idea finalized — AI Signal Platform, one-screen terminal
- [ ] SoSoValue API integration layer working
- [ ] AI agent generating test signals
- [ ] Frontend terminal layout built
- [ ] Live signals flowing into dashboard
- [ ] SoDEX trade button wired up
- [ ] Subscription contract deployed
- [ ] Demo recorded + submitted to Akindo
