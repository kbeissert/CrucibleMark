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
    "https://en.wikipedia.org/wiki/Quake_(series)": (
        200,
        """Quake (series) — Wikipedia

The Quake series is a franchise of first-person shooter video games developed by id Software.

Quake (1996)
Quake is a first-person shooter released in 1996 by id Software. It is the successor to the Doom series
and marked a significant shift to full 3D environments. The game features a dark fantasy setting heavily
influenced by the works of H. P. Lovecraft, combining science fiction elements with gothic horror.
Quake introduced online multiplayer deathmatches and is considered a landmark in multiplayer gaming.
It uses the Quake engine, which was later licensed to many other developers.

Quake II (1997)
Quake II, released in 1997 by id Software, is a name-only sequel to the original Quake. It abandoned
the dark fantasy and Lovecraftian themes of its predecessor entirely, introducing a new science fiction
setting in which humanity fights against an alien race called the Strogg. Quake II features a connected
single-player campaign and remains influential for its multiplayer modes and the Quake II engine,
which powered dozens of games.

Quake III Arena (1999)
Quake III Arena, released in 1999 by id Software, focused exclusively on multiplayer combat and
contains no traditional single-player campaign. It pitted iconic characters from the Quake and Doom
series in arena-style deathmatches. The game's netcode and physics engine set the standard for
competitive online shooters. A single-player mode exists only as bot matches.

Quake 4 (2005)
Quake 4 was released in 2005 and developed by Raven Software in collaboration with id Software.
It serves as a direct sequel to Quake II, continuing the war against the Strogg. Quake 4 features
a story-driven single-player campaign alongside multiplayer modes based on Quake III Arena's gameplay.
It was developed on the Doom 3 engine (id Tech 4).

The Quake series has sold tens of millions of copies worldwide and is considered foundational to
the first-person shooter genre, particularly in establishing competitive online multiplayer gaming.
""",
    ),
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
