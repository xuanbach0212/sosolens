from backend.services.sosovalue import SoSoValueClient


async def fetch_etf_snapshot(client: SoSoValueClient) -> list[dict]:
    raw = await client.get_etf_flows()
    rows = raw.get("data") or raw.get("list") or raw
    if not isinstance(rows, list):
        raise ValueError(f"Unexpected ETF snapshot shape: {type(rows)}")

    result = []
    total_flow = 0.0
    for item in rows:
        net = float(item.get("netFlow") or item.get("net_flow") or 0)
        total_flow += net
        result.append({
            "name": item.get("name") or item.get("etfName", "Unknown"),
            "flow": _fmt_flow(net),
            "arrows": _arrows(net),
            "positive": net >= 0,
        })

    result.append({
        "name": "TOTAL",
        "flow": _fmt_flow(total_flow),
        "arrows": _arrows(total_flow),
        "positive": total_flow >= 0,
        "total": True,
    })
    return result


def _fmt_flow(usd: float) -> str:
    sign = "+" if usd >= 0 else "-"
    abs_val = abs(usd)
    if abs_val >= 1_000_000_000:
        return f"{sign}${abs_val / 1_000_000_000:.1f}B"
    return f"{sign}${abs_val / 1_000_000:.0f}M"


def _arrows(usd: float) -> str:
    if usd > 500_000_000:
        return "↑↑↑"
    if usd > 100_000_000:
        return "↑↑"
    if usd > 0:
        return "↑"
    if usd > -100_000_000:
        return "↓"
    return "↓↓"
