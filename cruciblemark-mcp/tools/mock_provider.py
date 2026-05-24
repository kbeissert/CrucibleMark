"""Mock fixture provider — returns deterministic responses for CI/dev without network access."""

import uuid
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_request_id() -> str:
    """Return a new UUID4 string for request tracking."""
    return str(uuid.uuid4())


_FIXTURE_SEARCH: dict[str, list[dict]] = {
    "_default": [
        {
            "url": "https://huggingface.co/blog/open-llm-leaderboard",
            "title": "Open LLM Leaderboard — HuggingFace",
            "excerpt": "The Open LLM Leaderboard tracks and evaluates open-source large language models across benchmarks.",
        },
        {
            "url": "https://llama.meta.com/",
            "title": "Llama — Meta AI",
            "excerpt": "Meta's Llama is a family of large language models available for research and commercial use.",
        },
        {
            "url": "https://raw.githubusercontent.com/openai/evals/main/README.md",
            "title": "OpenAI Evals — GitHub",
            "excerpt": "A framework for evaluating OpenAI models and an open-source registry of evals.",
        },
    ],
}

_FIXTURE_FETCH: dict[str, tuple[int, str]] = {
    "https://huggingface.co/": (200, "Hugging Face – The AI community building the future."),
    "https://huggingface.co/meta-llama": (
        200,
        """Meta Llama – Hugging Face Organization

Models by Meta Llama (huggingface.co/meta-llama)

Llama 4 Scout
  Model: Llama-4-Scout-17B-16E-Instruct
  Type:  Image-Text to Text | 17B parameters | 16 experts (MoE)
  Meta's latest multimodal model combining vision and language.
  Requires a Meta license agreement to download and use.

Llama 4 Maverick
  Model: Llama-4-Maverick-17B-128E-Instruct
  Type:  Image-Text to Text | 17B parameters | 128 experts (MoE)
  Larger expert variant of Llama 4 for complex multimodal tasks.

Llama 3.3 70B Instruct
  Model: Llama-3.3-70B-Instruct
  Type:  Text to Text | 70B parameters
  High-performance text model; most downloaded in the Llama 3.x series.

Llama 3.2 Vision 11B Instruct
  Model: Llama-3.2-11B-Vision-Instruct
  Type:  Image-Text to Text | 11B parameters
  Multimodal model supporting image and text inputs.

Llama Guard 4
  Model: Llama-Guard-4-12B
  Type:  Image-Text to Text | 12B parameters | Safety model
  Content moderation and safety filtering for AI applications.

Llama 3.1 8B Instruct
  Model: Meta-Llama-3.1-8B-Instruct
  Type:  Text to Text | 8B parameters
  Compact, widely deployed base model for text generation.

All Llama models require acceptance of Meta's Llama license.
Commercial use is permitted under the respective license terms.
""",
    ),
    "https://llama.meta.com/": (200, "Llama is Meta's open foundation and fine-tuned chat models."),
    "https://raw.githubusercontent.com/openai/evals/main/README.md": (
        200,
        "# OpenAI Evals\nEvals is a framework for evaluating LLMs and an open-source registry.",
    ),
    "https://httpbin.org/get": (200, '{"args": {}, "headers": {}, "url": "https://httpbin.org/get"}'),
}


def mock_web_search(query: str, max_results: int, provider: str) -> dict:
    """Return a deterministic fixture response for web_search (mock mode)."""
    key = query.lower()
    results = _FIXTURE_SEARCH.get(key, _FIXTURE_SEARCH["_default"])
    return {
        "status": "success",
        "results": results[:max_results],
        "request_id": new_request_id(),
        "provider": provider,
        "timestamp": _now(),
    }


def mock_http_fetch(url: str, max_chars: int) -> dict:
    """Return a deterministic fixture response for http_fetch (mock mode)."""
    timestamp = _now()

    # 404 simulation — any URL containing /status/404
    if "/status/404" in url or url.endswith("/404"):
        return {
            "status": "error",
            "status_code": 404,
            "content_excerpt": None,
            "source_url": url,
            "request_id": new_request_id(),
            "timestamp": timestamp,
        }

    status_code, content = _FIXTURE_FETCH.get(url, (200, f"Mock content for {url}"))
    return {
        "status": "success",
        "status_code": status_code,
        "content_excerpt": content[:max_chars],
        "source_url": url,
        "request_id": new_request_id(),
        "timestamp": timestamp,
    }
