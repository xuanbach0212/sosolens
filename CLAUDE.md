# CLAUDE.md — Akindo × SoSoValue WaveHack

## Hackathon Context

| Field | Detail |
|-------|--------|
| **Event** | Build Your One-Person On-Chain Finance Business with SoSoValue |
| **Platform** | Akindo WaveHack (wave-based, not one-shot) |
| **URL** | https://app.akindo.io/wave-hacks/JBEQXgN4Zi2jA3wA |
| **Prize Pool** | ~10,000 USDC |
| **Competitors** | ~470 builders |
| **Tags** | #SoSoValue #SoDEX #ValueChain #Agentic #One-Person #On-Chain Finance #AI x Web3 |
| **API Docs** | https://sosovalue.gitbook.io/soso-value-api-doc/ |
| **SSI Protocol** | https://github.com/SoSoValueLabs/ssi-protocol |
| **Whitepaper** | https://sosovalue-white-paper.gitbook.io/sosovalue-whitepaper |

## WaveHack Format (Critical)

WaveHack is NOT a traditional one-shot hackathon:
- Runs in repeating **waves** (build period + voting period per wave)
- Grants distributed by **community votes** — more votes = more USDC
- Projects can compete across **multiple waves** (continuous improvement rewarded)
- Judging weights: tangible progress, GitHub activity, product updates, ecosystem impact
- A 10% protocol fee is deducted from each wave's distribution

**Winning strategy**: ship fast, iterate every wave, demonstrate real usage and on-chain activity.

## SoSoValue Stack Available to Build On

### Data API (REST/JSON, rate limit: 20 calls/min on free tier)
9 modules available:
1. **Currency & Pairs** — klines, market data, trading pairs, supply
2. **ETF** — crypto ETF summaries, market snapshots, historical data
3. **SoSoValue Index** — custom indices, constituents, market snapshots
4. **Crypto Stocks** — public crypto-sector companies, market cap, sector
5. **BTC Treasuries** — corporate Bitcoin holdings, acquisition history
6. **Feeds** — news feed, hot news, featured news, multilingual, by currency
7. **Fundraising** — project funding rounds and capital raise data
8. **Macro** — economic calendars, interest-rate trackers, liquidity indicators
9. **Analysis Charts** — charting datasets for technical analysis

### SSI Protocol (On-Chain)
- Solidity smart contracts (Foundry), deployed on EVM
- Wraps multi-chain, multi-asset portfolios into **Wrapped Index Tokens (SSI)**
- Tokens track value of underlying basket → passive index investing, on-chain
- Repo: `SoSoValueLabs/ssi-protocol` (Solidity 69%, JS 24%, Python 3%)

### SoDEX
- Decentralized exchange on ValueChain (SoSoValue's own L1)
- Order-book model, on-chain settlement
- Integration target for trading-related projects

### ValueChain
- SoSoValue's proprietary Layer-1 blockchain
- $SOSO is native gas + governance token
- Home of SoDEX

## Project Structure

```
contracts/      → Solidity smart contracts (Foundry)
frontend/       → Next.js web app (Wagmi + Viem for web3)
scripts/        → Deploy scripts and automation
docs/           → Architecture, plan, research notes
  plan.md       → Project plan and milestones
  research/     → Hackathon research and brainstorm
```

## Tech Stack Decisions

- **Smart Contracts**: Foundry (matches SSI Protocol repo)
- **Frontend**: Next.js + Tailwind + Wagmi v2 + Viem
- **Chain**: EVM-compatible (Base or Ethereum mainnet, or ValueChain if bridged)
- **AI/Agent layer**: Python or TypeScript AI agent using SoSoValue API
- **Package manager**: npm

## Dev Commands

```bash
# Smart contracts
cd contracts && forge build
cd contracts && forge test
cd contracts && forge script scripts/Deploy.s.sol --rpc-url $RPC_URL

# Frontend
cd frontend && npm run dev
cd frontend && npm run build

# Tests
npm test
```

## Environment Variables

Never commit `.env`. Required keys:
```
SOSOVALUE_API_KEY=
PRIVATE_KEY=          # deployer wallet
RPC_URL=              # target chain RPC
NEXT_PUBLIC_CHAIN_ID=
```

## Judging Criteria (How to Win)

1. **Deep SoSoValue integration** — use their APIs and/or SSI Protocol, not just superficially
2. **Real on-chain activity** — deployed contracts, actual transactions, live demo
3. **"One-person business" narrative** — clear how a solo operator earns revenue on-chain
4. **Agentic/AI angle** — #Agentic tag is prominent; automation is rewarded
5. **GitHub activity** — judges look at commit history, progress, and updates each wave
6. **Community votes** — write good updates, engage in the Akindo community

## Principles for This Project

- Ship a working MVP first; polish later
- Every wave: write a progress update on Akindo with screenshots/demo links
- Prioritize on-chain verifiability over off-chain logic
- Keep the "one person" angle clear in all copy and demos
- Use SoSoValue API for data — don't pull from CoinGecko or similar
