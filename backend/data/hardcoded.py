SIGNALS: list[dict] = [
    {
        "id": "ai-sector",
        "type": "BUY",
        "sector": "AI Sector",
        "confidence": 80,
        "risk": "MEDIUM",
        "timeAgo": "2h",
        "explanation": "ETF inflows into AI tokens spiked 40% this week while price hasn't reacted. Historically, price follows inflows in 3–5 days. BTC treasuries stable → macro not bearish. No negative news.",
        "dataSources": [
            {"name": "ETF Net Inflow (7d)", "value": "+$240M", "signal": "🟢", "arrow": "↑↑"},
            {"name": "Sector Capital Flow", "value": "Inflow", "signal": "🟢", "arrow": "↑"},
            {"name": "Macro Environment", "value": "Risk-On", "signal": "🟢"},
            {"name": "News Sentiment", "value": "Neutral", "signal": "⚪"},
            {"name": "BTC Treasuries", "value": "Stable", "signal": "⚪"},
            {"name": "VC Fundraising", "value": "2 rounds", "signal": "🟡"},
            {"name": "Price vs Flow Gap", "value": "Large", "signal": "🟢", "arrow": "↑↑"},
        ],
        "topTokens": [
            {"symbol": "FET", "price": "$2.41", "change": "+3.2%", "positive": True},
            {"symbol": "RNDR", "price": "$8.12", "change": "+4.5%", "positive": True},
            {"symbol": "AGIX", "price": "$1.23", "change": "+2.1%", "positive": True},
            {"symbol": "NEAR", "price": "$7.82", "change": "+1.1%", "positive": True},
            {"symbol": "TAO", "price": "$412.0", "change": "+2.8%", "positive": True},
            {"symbol": "FLock", "price": "$0.84", "change": "+1.9%", "positive": True},
        ],
        "pastSignals": [
            {"date": "Feb 14", "label": "AI BUY", "result": "+18% over 5d", "success": True},
            {"date": "Mar 02", "label": "AI BUY", "result": "+12% over 4d", "success": True},
            {"date": "Apr 11", "label": "AI BUY", "result": "-3% over 5d", "success": False},
        ],
        "accuracy": 67,
        "sodexPair": "BUY FET/USDC",
        "sodexSlippage": "1%",
        "sodexEstOutput": "41.5 FET per $100",
    },
    {
        "id": "defi-sector",
        "type": "WATCH",
        "sector": "DeFi Sector",
        "confidence": 65,
        "risk": "LOW",
        "timeAgo": "5h",
        "explanation": "VC activity picked up with 3 new funding rounds totaling $48M this week. Capital rotation into DeFi from L2 signals smart money repositioning. Price action flat — no breakout yet.",
        "dataSources": [
            {"name": "VC Fundraising (7d)", "value": "$48M, 3 rounds", "signal": "🟢", "arrow": "↑"},
            {"name": "Sector Capital Flow", "value": "Neutral", "signal": "⚪"},
            {"name": "Macro Environment", "value": "Risk-On", "signal": "🟢"},
            {"name": "News Sentiment", "value": "Positive", "signal": "🟢"},
            {"name": "ETF Net Inflow", "value": "+$42M", "signal": "🟡"},
            {"name": "Price Momentum", "value": "Flat", "signal": "⚪"},
        ],
        "topTokens": [
            {"symbol": "UNI", "price": "$12.40", "change": "+0.8%", "positive": True},
            {"symbol": "AAVE", "price": "$183.20", "change": "+1.2%", "positive": True},
            {"symbol": "CRV", "price": "$0.58", "change": "-0.4%", "positive": False},
            {"symbol": "MKR", "price": "$1,842", "change": "+0.3%", "positive": True},
            {"symbol": "LDO", "price": "$2.11", "change": "+1.5%", "positive": True},
            {"symbol": "COMP", "price": "$62.40", "change": "+0.2%", "positive": True},
        ],
        "pastSignals": [
            {"date": "Jan 28", "label": "DeFi WATCH", "result": "+9% over 7d", "success": True},
            {"date": "Mar 15", "label": "DeFi WATCH", "result": "+4% over 5d", "success": True},
            {"date": "Apr 03", "label": "DeFi WATCH", "result": "-6% over 5d", "success": False},
        ],
        "accuracy": 67,
        "sodexPair": "BUY UNI/USDC",
        "sodexSlippage": "0.5%",
        "sodexEstOutput": "8.1 UNI per $100",
    },
    {
        "id": "layer2",
        "type": "AVOID",
        "sector": "Layer 2",
        "confidence": 85,
        "risk": "HIGH",
        "timeAgo": "1d",
        "explanation": "ETF outflows from L2 tokens accelerating — $89M net outflow over 7 days. VC activity dried up. Macro rate uncertainty adding pressure. Smart money rotating out.",
        "dataSources": [
            {"name": "ETF Net Inflow (7d)", "value": "-$89M", "signal": "🔴", "arrow": "↓↓"},
            {"name": "Sector Capital Flow", "value": "Outflow", "signal": "🔴", "arrow": "↓"},
            {"name": "VC Fundraising", "value": "0 rounds", "signal": "🔴"},
            {"name": "News Sentiment", "value": "Negative", "signal": "🔴"},
            {"name": "Macro Environment", "value": "Neutral", "signal": "🟡"},
            {"name": "Price Momentum", "value": "Declining", "signal": "🔴", "arrow": "↓"},
        ],
        "topTokens": [
            {"symbol": "OP", "price": "$2.81", "change": "-5.2%", "positive": False},
            {"symbol": "ARB", "price": "$1.08", "change": "-4.8%", "positive": False},
            {"symbol": "MATIC", "price": "$0.82", "change": "-3.1%", "positive": False},
            {"symbol": "IMX", "price": "$2.40", "change": "-2.9%", "positive": False},
            {"symbol": "STRK", "price": "$0.72", "change": "-6.1%", "positive": False},
            {"symbol": "ZK", "price": "$0.18", "change": "-4.3%", "positive": False},
        ],
        "pastSignals": [
            {"date": "Feb 20", "label": "L2 AVOID", "result": "-14% over 7d", "success": True},
            {"date": "Mar 30", "label": "L2 AVOID", "result": "-8% over 5d", "success": True},
        ],
        "accuracy": 100,
        "sodexPair": "SELL OP/USDC",
        "sodexSlippage": "1.2%",
        "sodexEstOutput": "35.6 USDC per $100",
    },
    {
        "id": "btc",
        "type": "WATCH",
        "sector": "BTC",
        "confidence": 55,
        "risk": "LOW",
        "timeAgo": "2d",
        "explanation": "BTC ETF inflows strong at $570M weekly. Corporate treasury purchases continue. However, FOMC meeting in 7 days introduces macro uncertainty — wait for clearer signal post-Fed.",
        "dataSources": [
            {"name": "ETF Net Inflow (7d)", "value": "+$570M", "signal": "🟢", "arrow": "↑↑↑"},
            {"name": "BTC Treasuries", "value": "+1,282 BTC", "signal": "🟢", "arrow": "↑"},
            {"name": "Macro Event Risk", "value": "FOMC in 7d", "signal": "🟡"},
            {"name": "News Sentiment", "value": "Positive", "signal": "🟢"},
            {"name": "Price Momentum", "value": "Stable", "signal": "⚪"},
            {"name": "Fear/Greed", "value": "72 Greed", "signal": "🟡"},
        ],
        "topTokens": [
            {"symbol": "BTC", "price": "$98,420", "change": "+2.1%", "positive": True},
            {"symbol": "WBTC", "price": "$98,380", "change": "+2.1%", "positive": True},
            {"symbol": "cbBTC", "price": "$98,390", "change": "+2.0%", "positive": True},
        ],
        "pastSignals": [
            {"date": "Jan 10", "label": "BTC WATCH", "result": "+22% over 14d", "success": True},
            {"date": "Mar 05", "label": "BTC WATCH", "result": "+6% over 7d", "success": True},
            {"date": "Apr 22", "label": "BTC WATCH", "result": "-4% over 5d", "success": False},
        ],
        "accuracy": 67,
        "sodexPair": "BUY BTC/USDC",
        "sodexSlippage": "0.3%",
        "sodexEstOutput": "0.00102 BTC per $100",
    },
    {
        "id": "rwa",
        "type": "WATCH",
        "sector": "RWA Sector",
        "confidence": 60,
        "risk": "LOW",
        "timeAgo": "3d",
        "explanation": "Real-world asset tokenization narrative gaining momentum with $15M VC round this week. Regulatory clarity improving. Inflows modest but consistent.",
        "dataSources": [
            {"name": "VC Fundraising (7d)", "value": "$15M, 1 round", "signal": "🟢"},
            {"name": "Sector Capital Flow", "value": "+$18M", "signal": "🟢", "arrow": "↑"},
            {"name": "Regulatory News", "value": "Positive", "signal": "🟢"},
            {"name": "Macro Environment", "value": "Risk-On", "signal": "🟢"},
            {"name": "ETF Net Inflow", "value": "N/A", "signal": "⚪"},
            {"name": "Price Momentum", "value": "Moderate", "signal": "🟡"},
        ],
        "topTokens": [
            {"symbol": "ONDO", "price": "$1.42", "change": "+3.8%", "positive": True},
            {"symbol": "POLY", "price": "$0.68", "change": "+1.2%", "positive": True},
            {"symbol": "CFG", "price": "$0.42", "change": "+0.9%", "positive": True},
            {"symbol": "TRU", "price": "$0.14", "change": "+2.1%", "positive": True},
        ],
        "pastSignals": [
            {"date": "Feb 08", "label": "RWA WATCH", "result": "+11% over 10d", "success": True},
            {"date": "Apr 01", "label": "RWA WATCH", "result": "+5% over 7d", "success": True},
        ],
        "accuracy": 100,
        "sodexPair": "BUY ONDO/USDC",
        "sodexSlippage": "0.8%",
        "sodexEstOutput": "70.4 ONDO per $100",
    },
]

SIGNAL_STATS: dict = {"today": 3, "thisWeek": 14, "accuracy": 71}

MARKET_STATUS: dict = {
    "sentiment": "RISK-ON",
    "sentimentPositive": True,
    "btcPrice": "$98,420",
    "btcChange": "+2.1%",
    "ethPrice": "$3,210",
    "ethChange": "+1.8%",
    "mcap": "$3.42T",
    "mcapChange": "+1.9%",
    "vol": "$124B",
    "volChange": "+12%",
    "fearGreed": 72,
    "fearGreedLabel": "GREED",
}

SECTOR_FLOWS: list[dict] = [
    {"name": "AI/ML", "change": 40},
    {"name": "DeFi", "change": 27},
    {"name": "RWA", "change": 18},
    {"name": "L1", "change": 8},
    {"name": "BTC", "change": 5},
    {"name": "Stables", "change": 1},
    {"name": "L2", "change": -5},
    {"name": "Gaming", "change": -14},
    {"name": "NFT", "change": -22},
]

ETF_FLOWS: list[dict] = [
    {"name": "BTC ETF", "flow": "+$380M", "arrows": "↑↑↑", "positive": True},
    {"name": "ETH ETF", "flow": "+$120M", "arrows": "↑↑", "positive": True},
    {"name": "SOL ETF", "flow": "+$42M", "arrows": "↑", "positive": True},
    {"name": "Other", "flow": "+$28M", "arrows": "↑", "positive": True},
    {"name": "TOTAL", "flow": "+$570M", "arrows": "↑↑↑", "positive": True, "total": True},
]

MACRO_STATUS: list[dict] = [
    {"name": "Fed Rate", "value": "5.25%", "arrow": "→"},
    {"name": "US CPI", "value": "3.2%", "arrow": "↓"},
    {"name": "DXY", "value": "104.2", "arrow": "↓"},
    {"name": "10Y Yield", "value": "4.31%", "arrow": "↑"},
    {"name": "M2 Supply", "value": "↑ expand", "arrow": ""},
    {"name": "FOMC", "value": "in 7d", "arrow": "⚠️", "warning": True},
    {"name": "CPI", "value": "in 12d", "arrow": ""},
]

BTC_TREASURIES: list[dict] = [
    {"company": "MicroStrategy", "btcHeld": "214,246 BTC", "weeklyChange": "+1,282", "positive": True},
    {"company": "Marathon", "btcHeld": "40,435 BTC", "weeklyChange": "±0", "positive": None},
    {"company": "Tesla", "btcHeld": "11,509 BTC", "weeklyChange": "±0", "positive": None},
]

VC_ACTIVITY: list[dict] = [
    {"sector": "DeFi", "rounds": 3, "totalUsd": "$48M"},
    {"sector": "AI", "rounds": 2, "totalUsd": "$31M"},
    {"sector": "RWA", "rounds": 1, "totalUsd": "$15M"},
]

AI_BRIEFING: list[str] = [
    "ETF inflows hit 2-month high ($570M). Last time this happened BTC +12% in 5d.",
    "Fed minutes tonight 18:00 UTC — AI sector drops avg 8% if hawkish. De-risk.",
    "DeFi VC: 3 new rounds this week signals smart money rotating from L2 → DeFi.",
]

NEWS_HEADLINES: list[dict] = [
    {"text": "BlackRock BTC ETF records $380M single-day inflow", "source": "Bloomberg"},
    {"text": "Paradigm leads $31M raise in AI infra protocol", "source": "The Block"},
    {"text": "Fed officials signal patience on rate cuts", "source": "Reuters", "macroSensitive": True},
]
