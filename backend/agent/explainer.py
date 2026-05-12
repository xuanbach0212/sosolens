import asyncio
import json
import logging
import os

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a crypto market analyst. "
    "Explain a trading signal in 2–3 plain-English sentences. "
    "Be specific about the data points driving the signal. "
    "No bullet points. No markdown. No disclaimers."
)

_anthropic_client = None
_openai_client = None
_openrouter_client = None
_gemini_client = None


def _build_provider_list() -> list[str]:
    known = {"anthropic", "openai", "openrouter", "gemini"}
    raw = os.environ.get("AI_PROVIDERS", "anthropic")
    providers = [p.strip() for p in raw.split(",") if p.strip()]
    result = []
    for p in providers:
        if p in known:
            result.append(p)
        else:
            logger.warning("[explainer] unknown provider %r — skipping", p)
    return result or ["anthropic"]


async def _try_anthropic(summary: dict) -> str | None:
    global _anthropic_client
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from anthropic import AsyncAnthropic
        if _anthropic_client is None:
            _anthropic_client = AsyncAnthropic(api_key=api_key)
        response = await _anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            system=_SYSTEM,
            messages=[{"role": "user", "content": json.dumps(summary)}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logger.warning("[explainer] anthropic failed: %s", exc)
        return None


async def _try_openai(summary: dict) -> str | None:
    global _openai_client
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import AsyncOpenAI
        if _openai_client is None:
            _openai_client = AsyncOpenAI(api_key=api_key)
        response = await _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=150,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": json.dumps(summary)},
            ],
        )
        return response.choices[0].message.content.strip()
    except ImportError:
        logger.warning("[explainer] openai package not installed — pip install openai")
        return None
    except Exception as exc:
        logger.warning("[explainer] openai failed: %s", exc)
        return None


async def _try_openrouter(summary: dict) -> str | None:
    global _openrouter_client
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openrouter import OpenRouter
        if _openrouter_client is None:
            model = os.environ.get("OPENROUTER_MODEL", "z-ai/glm-4.5-air:free")
            _openrouter_client = (OpenRouter(api_key=api_key), model)
        client, model = _openrouter_client
        prompt = f"{_SYSTEM}\n\nSignal data:\n{json.dumps(summary)}\n\nWrite the explanation now:"
        response = client.chat.send(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        return content.strip() if content else None
    except ImportError:
        logger.warning("[explainer] openrouter package not installed — pip install openrouter")
        return None
    except Exception as exc:
        logger.warning("[explainer] openrouter failed: %s", exc)
        return None


async def _try_gemini(summary: dict) -> str | None:
    global _gemini_client
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        if _gemini_client is None:
            _gemini_client = genai.Client(api_key=api_key)
        prompt = f"{_SYSTEM}\n\n{json.dumps(summary)}"
        response = await _gemini_client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text.strip()
    except ImportError:
        logger.warning("[explainer] google-genai package not installed — pip install google-genai")
        return None
    except Exception as exc:
        logger.warning("[explainer] gemini failed: %s", exc)
        return None


_PROVIDER_FNS = {
    "anthropic": _try_anthropic,
    "openai": _try_openai,
    "openrouter": _try_openrouter,
    "gemini": _try_gemini,
}


async def explain_signal(signal_data: dict) -> str:
    summary = {
        "type": signal_data.get("type"),
        "sector": signal_data.get("sector"),
        "confidence": signal_data.get("confidence"),
        "risk": signal_data.get("risk"),
        "data": [
            {"source": ds.get("name"), "value": ds.get("value")}
            for ds in signal_data.get("dataSources", [])[:4]
        ],
    }

    for provider in _build_provider_list():
        result = await _PROVIDER_FNS[provider](summary)
        if result:
            return result

    return _fallback(signal_data)


def _fallback(signal_data: dict) -> str:
    sig_type = signal_data.get("type", "WATCH")
    sector = signal_data.get("sector", "unknown sector")
    sources = signal_data.get("dataSources", [])
    if sources:
        top = sources[0]
        return f"{sig_type} signal in {sector}: {top.get('name', '')} at {top.get('value', '')}."
    return f"{sig_type} signal detected in {sector}."
