interface Env {
  SOSOLENS_CACHE: KVNamespace;
  PUSH_SECRET: string;
  UPSTREAM_URL: string;
}

type Snapshot = Record<string, unknown>;

const CORS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, X-Push-Secret",
};

// Paths served from KV → their KV key
const PATH_TO_KV: Record<string, string> = {
  "/api/market": "endpoint:market",
  "/api/signals": "endpoint:signals",
  "/api/sector-flows": "endpoint:sector-flows",
  "/api/etf-flows": "endpoint:etf-flows",
  "/api/macro": "endpoint:macro",
  "/api/btc-treasuries": "endpoint:btc-treasuries",
  "/api/vc-activity": "endpoint:vc-activity",
  "/api/news": "endpoint:news",
};

// How to extract the right response shape from the full snapshot per KV key
function snapshotToEntries(snap: Snapshot): Array<[string, string]> {
  const entries: Array<[string, string]> = [];

  if (snap.market !== undefined) {
    entries.push([
      "endpoint:market",
      JSON.stringify({ market: snap.market, is_fallback: snap.is_fallback ?? false }),
    ]);
  }
  if (snap.signals !== undefined) {
    entries.push([
      "endpoint:signals",
      JSON.stringify({ signals: snap.signals, stats: snap.stats ?? {} }),
    ]);
  }
  if (snap.sectorFlows !== undefined) {
    entries.push(["endpoint:sector-flows", JSON.stringify({ sectorFlows: snap.sectorFlows })]);
  }
  if (snap.etfFlows !== undefined) {
    entries.push(["endpoint:etf-flows", JSON.stringify({ etfFlows: snap.etfFlows })]);
  }
  if (snap.macroStatus !== undefined) {
    entries.push([
      "endpoint:macro",
      JSON.stringify({
        macroStatus: snap.macroStatus,
        riskEnvironment: snap.riskEnvironment ?? "neutral",
        upcomingEvents: snap.upcomingEvents ?? [],
        macroStatusDetail: snap.macroStatusDetail ?? {},
      }),
    ]);
  }
  if (snap.btcTreasuries !== undefined) {
    entries.push(["endpoint:btc-treasuries", JSON.stringify({ btcTreasuries: snap.btcTreasuries })]);
  }
  if (snap.vcActivity !== undefined) {
    entries.push(["endpoint:vc-activity", JSON.stringify({ vcActivity: snap.vcActivity })]);
  }
  if (snap.aiBriefing !== undefined) {
    entries.push([
      "endpoint:news",
      JSON.stringify({ aiBriefing: snap.aiBriefing, newsHeadlines: snap.newsHeadlines ?? [] }),
    ]);
  }

  return entries;
}

function jsonResponse(body: string, status = 200): Response {
  return new Response(body, {
    status,
    headers: { "Content-Type": "application/json", ...CORS },
  });
}

function textResponse(body: string, status = 200): Response {
  return new Response(body, { status, headers: CORS });
}

async function proxyToUpstream(request: Request, upstreamUrl: string): Promise<Response> {
  const url = new URL(request.url);
  const target = `${upstreamUrl}${url.pathname}${url.search}`;
  const proxied = new Request(target, {
    method: request.method,
    headers: request.headers,
    body: request.body,
    // duplex needed for POST bodies in Workers
    // @ts-expect-error duplex is a valid fetch option in Workers
    duplex: "half",
  });
  const resp = await fetch(proxied);
  const headers = new Headers(resp.headers);
  Object.entries(CORS).forEach(([k, v]) => headers.set(k, v));
  return new Response(resp.body, { status: resp.status, headers });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS preflight
    if (request.method === "OPTIONS") {
      return textResponse("", 204);
    }

    // Push from Pi backend
    if (path === "/api/push" && request.method === "POST") {
      if (request.headers.get("X-Push-Secret") !== env.PUSH_SECRET) {
        return textResponse("Unauthorized", 401);
      }
      let snap: Snapshot;
      try {
        snap = (await request.json()) as Snapshot;
      } catch {
        return textResponse("Bad JSON", 400);
      }
      const entries = snapshotToEntries(snap);
      await Promise.all(entries.map(([key, value]) => env.SOSOLENS_CACHE.put(key, value)));
      return textResponse(`ok — ${entries.length} keys updated`);
    }

    // Cached GET endpoints — serve from KV, fall back to Pi on miss
    if (request.method === "GET") {
      const kvKey = PATH_TO_KV[path];
      if (kvKey) {
        const cached = await env.SOSOLENS_CACHE.get(kvKey);
        if (cached !== null) {
          return jsonResponse(cached);
        }
        // Cold start: fetch from Pi and warm the cache
        const upstream = await fetch(`${env.UPSTREAM_URL}${path}${url.search}`);
        if (upstream.ok) {
          const body = await upstream.text();
          await env.SOSOLENS_CACHE.put(kvKey, body);
          return jsonResponse(body);
        }
        return textResponse("upstream unavailable", 503);
      }
    }

    // Everything else: proxy to Pi (SSE, subscription, etf-history, price-history, etc.)
    return proxyToUpstream(request, env.UPSTREAM_URL);
  },
};
