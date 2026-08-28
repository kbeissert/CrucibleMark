"""Mock fixture provider — returns deterministic responses for CI/dev without network access."""

import uuid
from datetime import datetime, UTC


def _now() -> str:
    return datetime.now(UTC).isoformat()


def new_request_id() -> str:
    """Return a new UUID4 string for request tracking."""
    return str(uuid.uuid4())


_FIXTURE_SEARCH: dict[str, list[dict]] = {
    "_default": [
        {
            "url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard",
            "title": "Open LLM Leaderboard — HuggingFace",
            "excerpt": (
                "The Open LLM Leaderboard evaluates open-source large language models on standardized "
                "benchmarks including MMLU, HellaSwag, ARC, and TruthfulQA. Currently top-ranked "
                "open-weight models include Llama 3.1 405B, Qwen2.5 72B, and Mistral Large. "
                "All evaluated models are freely downloadable from HuggingFace."
            ),
        },
        {
            "url": "https://llama.meta.com/",
            "title": "Llama — Meta AI",
            "excerpt": (
                "Meta's Llama 3 family — Llama 3.1 (8B, 70B, 405B) and Llama 3.2 (multimodal, 1B–90B) "
                "— ranks among the best open-source models on standard benchmarks. Available on "
                "HuggingFace and via Meta's download page under the Llama community license, "
                "which permits commercial use for most organizations."
            ),
        },
        {
            "url": "https://huggingface.co/mistralai",
            "title": "Mistral AI — HuggingFace",
            "excerpt": (
                "Mistral AI offers a range of open-weight models: Mistral 7B, Mixtral 8x7B (MoE), "
                "and Mistral Large. These models are available on HuggingFace under the Apache 2.0 "
                "license and consistently place in the top tier of open-source LLM benchmarks, "
                "particularly for instruction-following and coding tasks."
            ),
        },
    ],
}

_FIXTURE_FETCH: dict[str, tuple[int, str]] = {
    "https://huggingface.co/": (200, "Hugging Face – The AI community building the future."),
    "https://huggingface.co/meta-llama": (
        200,
        """meta-llama/Llama-4-Scout-17B-16E-Instruct
Image-Text-to-Text • Updated • 409k • 1.29k
meta-llama/Llama-4-Scout-17B-16E
Image-Text-to-Text • Updated • 13.2k • 244
meta-llama/Llama-4-Maverick-17B-128E-Instruct
Image-Text-to-Text • 402B • Updated • 37.7k • 487
meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8
Image-Text-to-Text • 402B • Updated • 117k • 168

The Llama Family
From Meta
Welcome to the official Hugging Face organization for Llama, Llama Guard, and Prompt Guard models from Meta!
In order to access models here, please visit a repo of one of the three families and accept the license terms and acceptable use policy. Requests are processed hourly.

Current:
Llama 4: The Llama 4 collection of models are natively multimodal AI models that enable text and multimodal experiences. These models leverage a mixture-of-experts architecture to offer industry-leading performance in text and image understanding.
These Llama 4 models mark the beginning of a new era for the Llama ecosystem. We are launching two efficient models in the Llama 4 series, Llama 4 Scout, a 17 billion parameter model with 16 experts, and Llama 4 Maverick, a 17 billion parameter model with 128 experts.

History:
- Llama 3.3: The Llama 3.3 is a text only instruct-tuned model in 70B size (text in/text out).
- Llama 3.2: The Llama 3.2 collection of multilingual large language models (LLMs) is a collection of pretrained and instruction-tuned generative models in 1B and 3B sizes (text in/text out).
- Llama 3.2 Vision: The Llama 3.2-Vision collection of multimodal large language models (LLMs) is a collection of pretrained and instruction-tuned image reasoning generative models in 11B and 90B sizes (text + images in / text out)
- Llama 3.1: a collection of pretrained and fine-tuned text models with sizes ranging from 8 billion to 405 billion parameters pre-trained on ~15 trillion tokens.
- Llama 2: a collection of pretrained and fine-tuned text models ranging in scale from 7 billion to 70 billion parameters.
- Code Llama: a collection of code-specialized versions of Llama 2.
- Llama Guard: a 8B Llama 3 safeguard model for classifying LLM inputs and responses.

Learn more about the models at https://ai.meta.com/llama/
""",
    ),
    "https://llama.meta.com/": (200, "Llama is Meta's open foundation and fine-tuned chat models."),
    "https://raw.githubusercontent.com/openai/evals/main/README.md": (
        200,
        "# OpenAI Evals\nEvals is a framework for evaluating LLMs and an open-source registry.",
    ),
    "https://httpbin.org/get": (200, '{"args": {}, "headers": {}, "url": "https://httpbin.org/get"}'),
    "https://en.wikipedia.org/wiki/Python_(programming_language)": (
        200,
        """Python (programming language) — Wikipedia

Python is a high-level, general-purpose programming language. Its design philosophy
emphasizes code readability through the use of significant indentation.

Python is dynamically typed and garbage-collected. It supports multiple programming
paradigms, including structured, object-oriented, and functional programming.

Created by Guido van Rossum and first released in 1991, Python consistently ranks
among the most popular programming languages worldwide.

Key features:
- Readable, clean syntax with significant whitespace
- Dynamic typing and duck typing
- Extensive standard library ("batteries included")
- Large ecosystem of third-party packages via PyPI
- Interpreted language with an interactive REPL
- Multi-paradigm: procedural, object-oriented, functional
- Cross-platform compatibility

Python is widely used in web development, data science, artificial intelligence,
scientific computing, and automation. Python 3 is the current major version;
Python 2 reached end-of-life in January 2020.
""",
    ),
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
    selected = results[:max_results]
    content_text = f"Search results for '{query}':\n\n" + "\n\n".join(
        f"{r['title']}\n{r['url']}\n{r['excerpt']}" for r in selected
    )
    return {
        "status": "success",
        "results": selected,
        "content": [{"type": "text", "text": content_text}],
        "isError": False,
        "request_id": new_request_id(),
        "provider": provider,
        "timestamp": _now(),
    }


def mock_http_fetch(url: str, max_chars: int) -> dict:
    """Return a deterministic fixture response for http_fetch (mock mode)."""
    timestamp = _now()

    # 404 simulation — any URL containing /status/404
    if "/status/404" in url or url.endswith("/404"):
        error_text = f"Error fetching {url}: HTTP 404 Not Found"
        return {
            "status": "error",
            "status_code": 404,
            "content_excerpt": None,
            "content": [{"type": "text", "text": error_text}],
            "isError": True,
            "source_url": url,
            "request_id": new_request_id(),
            "timestamp": timestamp,
        }

    status_code, content = _FIXTURE_FETCH.get(url, (200, f"Mock content for {url}"))
    text = content[:max_chars]
    content_text = f"Contents of {url}:\n{text}"
    return {
        "status": "success",
        "status_code": status_code,
        "content_excerpt": text,
        "content": [{"type": "text", "text": content_text}],
        "isError": False,
        "source_url": url,
        "request_id": new_request_id(),
        "timestamp": timestamp,
    }
