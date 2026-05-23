"""Mock fixture provider — returns deterministic responses for CI/dev without network access."""

import uuid
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_request_id() -> str:
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
    ]
}

_FIXTURE_FETCH: dict[str, tuple[int, str]] = {
    "https://huggingface.co/": (200, "Hugging Face – The AI community building the future."),
    "https://llama.meta.com/": (200, "Llama is Meta's open foundation and fine-tuned chat models."),
    "https://raw.githubusercontent.com/openai/evals/main/README.md": (
        200,
        "# OpenAI Evals\nEvals is a framework for evaluating LLMs and an open-source registry.",
    ),
    "https://httpbin.org/get": (200, '{"args": {}, "headers": {}, "url": "https://httpbin.org/get"}'),
}


def mock_web_search(query: str, max_results: int, provider: str) -> dict:
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
