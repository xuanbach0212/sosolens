_SCORES: dict[tuple[str, str], dict] = {
    ("etf-flow-spike",        "BUY"):   {"confidence": 82, "risk": "MEDIUM"},
    ("etf-flow-spike",        "WATCH"): {"confidence": 62, "risk": "MEDIUM"},
    ("etf-flow-spike",        "AVOID"): {"confidence": 85, "risk": "HIGH"},
    ("sector-rotation",       "BUY"):   {"confidence": 76, "risk": "LOW"},
    ("sector-rotation",       "WATCH"): {"confidence": 58, "risk": "MEDIUM"},
    ("macro-risk-classifier", "BUY"):   {"confidence": 85, "risk": "LOW"},
    ("macro-risk-classifier", "WATCH"): {"confidence": 68, "risk": "MEDIUM"},
    ("macro-risk-classifier", "AVOID"): {"confidence": 88, "risk": "HIGH"},
}


def score_signal(raw_signal: dict) -> dict:
    key = (raw_signal.get("id", ""), raw_signal.get("type", ""))
    return dict(_SCORES.get(key, {"confidence": 50, "risk": "MEDIUM"}))
