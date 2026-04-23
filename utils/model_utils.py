"""
Utility functions for model management and filtering.
"""

import json
import logging
import re
import shutil
import subprocess
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional, TypeVar

logger = logging.getLogger(__name__)
from utils.constants import (
    MODEL_TYPE_OPEN_WEIGHTS_CLOUD,
    TIMEOUT_OLLAMA_VERSION,
    TIMEOUT_OLLAMA_LIST,
)

T = TypeVar("T")


def _extract_ollama_id(model_name: str, ollama_output: str) -> Optional[str]:
    """Extracts a model hash/ID from `ollama list` output for an exact model name match."""
    candidates = [model_name]
    if model_name.startswith("ollama/"):
        candidates.append(model_name.replace("ollama/", "", 1))

    for raw_line in ollama_output.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("name"):
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        listed_name = parts[0]
        listed_id = parts[1]

        if listed_name in candidates:
            return listed_id

    return None


def _get_local_model_hash_version(model_name: str) -> str:
    """Returns the local model hash (Ollama ID) as version; never a semantic label."""
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        return "k.A."

    try:
        result = subprocess.run(
            [ollama_path, "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=TIMEOUT_OLLAMA_VERSION,
        )
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return "k.A."

    model_id = _extract_ollama_id(model_name=model_name, ollama_output=result.stdout)
    if model_id and re.fullmatch(r"[a-f0-9]{6,64}", model_id):
        return model_id

    return "k.A."


def get_model_version(model_name: str, provider: str = "ollama", client=None) -> str:
    """
    Retrieves the uniform version mapping of a model without unpredictable fallback fingerprints.
    """
    _ = client  # API compatibility: kept for unchanged call sites.
    p_lower = str(provider).lower().strip()
    prefix = model_name.split("/")[0].lower() if "/" in model_name else ""

    # Attempt Local Ollama Logic if provider implies local, or no explicit provider is given
    is_local_attempt = (p_lower in {"ollama", "local"} or prefix in {"ollama", "local"} or p_lower == "ollama")

    if is_local_attempt:
        local_hash = _get_local_model_hash_version(model_name=model_name)
        if local_hash != "k.A.":
            return local_hash

    # Commercial Model Logic
    if "claude" in model_name:
        match = re.search(r"claude-\d+(?:-\w+)?-(202\d{5})", model_name)
        if match: return match.group(1)
        if "-4-7" in model_name: return "4.7"
        if "-4-6" in model_name: return "4.6"
        if "-4-5" in model_name: return "4.5"
        if "3-5" in model_name: return "3.5"
        if "haiku-20240307" in model_name: return "20240307"
    if "gpt" in model_name:
        match = re.search(r"-(202\d{5})$|-(0\d{3})$", model_name)
        if match: return match.group(1) or match.group(2)
        if "gpt-5.4" in model_name: return "5.4"
        if "gpt-5" in model_name: return "5.0"
        if "gpt-4o-mini" in model_name: return "2024-07-18"
        if "gpt-4o" in model_name: return "2024-05-13"
        return "latest"
    if "gemini" in model_name:
        if "3.1" in model_name: return "3.1-pro-preview"
        if "3-flash-preview" in model_name: return "3-flash-preview"
        if "flash" in model_name: return "2.5-flash"
        if "pro" in model_name: return "2.5-pro"
        return model_name.split("-")[-1]
    if "mistral" in model_name or "pixtral" in model_name:
        match = re.search(r"-(24\d{2})$", model_name)
        if match: return match.group(1)
        if "large" in model_name: return "2411"
        if "medium" in model_name: return "2312"
    if "grok" in model_name:
        match = re.search(r"grok-([0-9]+(?:\.[0-9]+)?(?:-[0-9]+)?)(?:-([^/]+))?", model_name)
        if match:
            version = match.group(1)
            suffix = match.group(2) or ""
            if "mini" in suffix:
                return f"{version}-mini"
            if "reasoning" in suffix and "non-reasoning" not in suffix:
                return f"{version}-reasoning"
            return version
        return "latest"
    if "kimi" in model_name:
        match = re.search(r"kimi-(k[\d\.]+)", model_name.lower())
        if match:
            return match.group(1)
        return "latest"
    if "llama" in model_name.lower():
        match = re.search(r"llama-?(\d+(?:\.\d+)?)-?(\d+b)?", model_name.lower())
        if match:
            version = match.group(1)
            size = match.group(2)
            if size:
                return f"{version}-{size.upper()}"
            return version
        return "latest"

    if "lfm" in model_name:
        return "latest"
    if "o1" in model_name or "o3" in model_name:
        match = re.search(r"o[13](?:-[a-z]+)*-(\d{4}-\d{2}-\d{2})", model_name)
        if match:
            return match.group(1)
        if "o3-mini" in model_name:
            return "2025-01-31"
        if model_name == "o1" or model_name.endswith("/o1"):
            return "2024-12-17"
        return "latest"
    return "k.A."


def format_version_hash_for_display(version: str, model_type: str = "") -> str:
    """
    Truncates local/Ollama model hashes to 6 characters for display purposes.
    Nur für die Anzeige im Leaderboard. Format: 6 Zeichen hex.
    """
    version = str(version).strip()
    m_type = str(model_type).strip().lower()

    # Check if we should treat it as a local/Ollama model (e.g. "Local", "Local Cloud")
    is_local_variant = ("local" in m_type or "ollama" in m_type or not m_type)

    if is_local_variant and len(version) > 6 and re.match(r"^[a-f0-9]+$", version):
        return version[:6]

    return version


def get_ollama_model_info(model_name: str) -> dict[str, Any]:
    """Holt Details (ID/Digest) zu einem bestimmten Ollama-Modell via CLI."""
    try:
        ollama_path = shutil.which("ollama")
        if not ollama_path:
            return {}

        # 'ollama list' ist effizienter als 'ollama show' für die ID
        result = subprocess.run(
            [ollama_path, "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=TIMEOUT_OLLAMA_LIST,
        )

        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[0] == model_name:
                return {"id": parts[1], "size": parts[2]}

        return {}

    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return {}


def is_model_suitable_for_benchmark(model_name: str) -> bool:
    """
    Determines if a model is suitable for text generation benchmarks.
    Filters out embedding models and other non-generative models.

    Args:
        model_name: Name of the model (e.g., 'nomic-embed-text:latest', 'llama3:8b')

    Returns:
        bool: True if model is suitable, False otherwise.
    """
    name_lower = model_name.lower()

    # Filter criteria
    if "embed" in name_lower:
        return False
    if "-vl" in name_lower:
        return False
    if "vision" in name_lower:
        return False

    # Add more exclusion criteria here if needed in the future

    return True


def get_ollama_models_info() -> list[dict[str, Any]]:
    """Holt und normalisiert Ollama-Modelle."""
    try:
        import ollama

        # Handle simplified response type if necessary or generic object access
        response = ollama.list()
        models = (
            response.models
            if hasattr(response, "models")
            else response.get("models", [])
        )

        results: list[dict[str, Any]] = []
        for m in models:
            # Access attributes safely (pydantic model vs dict)
            name = str(m.model) if hasattr(m, "model") else str(m.get("name", ""))
            if not is_model_suitable_for_benchmark(name):
                continue

            size = m.size if hasattr(m, "size") else m.get("size", 0)
            modified = (
                m.modified_at
                if hasattr(m, "modified_at")
                else m.get("modified_at", "N/A")
            )

            # Simple normalization
            modified_str = str(modified)[:10] if modified != "N/A" else "N/A"
            size_gb = (size or 0) / (1024**3)

            results.append(
                {
                    "name": name,
                    "size_gb": size_gb,
                    "modified": modified_str,
                    "original": m,  # keep object if needed
                }
            )

        return sorted(results, key=lambda x: x["name"])

    except (
        ImportError,
        subprocess.CalledProcessError,
        OSError,
        subprocess.TimeoutExpired,
    ):
        return []


def get_commercial_models_from_config(
    config: dict[str, Any],
) -> list[tuple[str, str, str]]:
    """
    Extracts enabled commercial models from the configuration dictionary.

    Args:
        config (dict): The loaded benchmark_config.yaml content.

    Returns:
        List[Tuple[str, str, str]]: List of (model_id, pretty_name, provider_key)
    """
    models: list[tuple[str, str, str]] = []
    providers = config.get("providers", {}).get("commercial", {})

    for p_key, p_config in providers.items():
        if p_config.get("enabled", False):
            for m in p_config.get("models", []):
                # model_id, name, provider
                models.append((m["id"], m["name"], p_key))

    return models


def resolve_provider(model_name: str) -> tuple[str, str]:
    """Ermittelt Provider basierend auf benchmark_config.yaml (SSOT), Fallback: Modell-Präfix."""

    # Determine if likely Ollama (contains tag separator)
    if ":" in model_name:
        return "ollama", model_name

    # SSOT: Lookup in benchmark_config.yaml
    _config_path = Path("benchmark_config.yaml")
    if _config_path.exists():
        try:
            with open(_config_path, encoding="utf-8") as _f:
                _cfg = yaml.safe_load(_f)
            for _prov_key, _prov_cfg in _cfg.get("providers", {}).get("commercial", {}).items():
                for _m in _prov_cfg.get("models", []):
                    if _m.get("id") == model_name:
                        return _prov_key, model_name
        except Exception:
            pass

    # Fallback: Präfix-Matching für nicht konfigurierte Modelle
    name_lower = model_name.lower()
    if name_lower.startswith(("mistral-", "open-mixtral", "ministral")):
        return "mistral", model_name
    if name_lower.startswith(("gpt-", "o1-", "o3-")) or name_lower in ("o1", "o3-mini"):
        return "openai", model_name
    if name_lower.startswith("claude-"):
        return "anthropic", model_name
    if name_lower.startswith("gemini-"):
        return "google", model_name
    if name_lower.startswith("grok-"):
        return "xai", model_name
    if "/" in name_lower or name_lower.startswith(("qwen", "llama", "moonshot")):
        return "groq", model_name

    # Default to local
    return "ollama", model_name


def is_cloud_model(model_name: str, size_gb: Optional[float] = None) -> bool:
    """
    SSOT: Determines if an Ollama model is a cloud proxy model.

    This is the canonical definition used across the entire codebase:
    - UI filtering (run_benchmark.py)
    - Data loading (data_loader.py)
    - Model categorization (get_model_category)

    Args:
        model_name: Name of the model (e.g., 'minimax-m2:cloud')
        size_gb: Optional model size in GB (if available)

    Returns:
        bool: True if model is a cloud proxy model

    Detection Rules:
        1. Model name contains ':cloud' tag (e.g., 'minimax-m2:cloud')
        2. Model name ends with '-cloud' suffix (e.g., 'gpt-oss:120b-cloud')
        3. Model size is extremely small (< 0.01 GB = proxy, not locally stored)
    """
    model_lower = model_name.lower()

    # Rule 1 & 2: Name-based detection
    if ":cloud" in model_lower or model_lower.endswith("-cloud"):
        return True

    # Rule 3: Size-based heuristic (proxy models have minimal/no local storage)
    if size_gb is not None and size_gb < 0.01:
        return True

    return False


def get_model_category(
    model_name: str, source_file: str = "local", size_gb: Optional[float] = None, provider: Optional[str] = None
) -> str:
    """
    Central SSOT for model categorization.
    Determines whether a model is Commercial, Local, or Local Cloud.

    Args:
        model_name: Name of the model (e.g., 'ministral-3:14b', 'gpt-oss:120b-cloud')
        source_file: Source CSV file ('local' or 'commercial')
        size_gb: Optional model size in GB (for better cloud detection)
        provider: Optional provider name (from config or CSV) to determine exact grouping

    Returns:
        str: 'Commercial', 'Local', 'Cloud-Modelle (Open-Weights)' or 'Local Cloud'
    """
    if provider:
        try:
            from utils.config_validator import ConfigValidator
            config = ConfigValidator().config
            commercial_providers = config.get("providers", {}).get("commercial", {})
            if provider in commercial_providers:
                m_type = commercial_providers[provider].get("model_type", "")
                if m_type == MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
                    return "Open Weights (Cloud)"
                elif m_type == "proprietary_api":
                    return "Proprietär"
                elif m_type == "cloud":
                    return "Open Weights (Local)"
        except Exception:
            pass

# Wenn neue cloud Datei oder aus lokaler CSV und der Name "cloud" enthaelt, soll es offene Cloud-Modelle abbilden
    if source_file == "cloud" or (source_file == "local" and ("cloud" in model_name.lower() or (size_gb is not None and size_gb < 0.01))):
        return "Open Weights (Cloud)"

    # Rule 1: Commercial CSV → Always Commercial
    if source_file == "commercial":
        return "Proprietär"

    # Rule 2: Local CSV → Check if it's a cloud proxy using canonical logic
    if is_cloud_model(model_name, size_gb):
        return "Open Weights (Cloud)"

    # Rule 3: Everything else from Local CSV → Local
    return "Open Weights (Local)"


def resolve_token_budget(
    model: str,
    requested_max_tokens: int | None,
    config: dict,
    module_key: str | None = None,
) -> tuple[int, bool]:
    """
    Berechnet das effektive Token-Budget für einen API-Request.

    Reasoning-Modelle (z.B. magistral, o1, minimax-m2) verbrauchen interne
    Thinking-Tokens gegen dasselbe max_tokens-Kontingent wie der sichtbare Output.
    Diese Funktion ersetzt das Standard-Budget durch den erhöhten Wert aus
    `token_budgets_reasoning_models` in benchmark_config.yaml.

    Args:
        model: Modell-ID (z.B. "magistral-medium-latest")
        requested_max_tokens: Vom base_runner injiziertes Modul-Budget (kann None sein)
        config: Vollständige benchmark_config (self.config im Provider)
        module_key: Modul-Schlüssel aus base_runner (z.B. "cultural_intelligence")

    Returns:
        tuple[int, bool]: (effektives_budget, is_reasoning)
    """
    reasoning = is_reasoning_model(model)
    explicit_budget = requested_max_tokens is not None
    tokens: int = requested_max_tokens or config.get("defaults", {}).get("generation", {}).get("num_predict", 8192)

    if reasoning and explicit_budget:
        budgets = config.get("token_budgets_reasoning_models", {})
        tokens = budgets[module_key] if (module_key and module_key in budgets) else tokens * 5
    elif reasoning and tokens < 10000:
        tokens = 25000

    return tokens, reasoning


def is_reasoning_model_from_card(model_id: str) -> bool | None:
    """
    Reads `thinking_probe_detected` from an existing model card JSON.

    Returns:
        True/False if the field is set; None if no card exists or field is missing.
    """
    card_path = Path("benchmark_scores/model_cards") / f"{re.sub(r'[:/.\ ]', '_', model_id)}.json"
    if not card_path.exists():
        return None
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        val = data.get("thinking_probe_detected")
        if val is None:
            return None
        return bool(val)
    except Exception:
        return None


def is_reasoning_model(model_name: str) -> bool:
    """
    Checks if the model is a reasoning model (Chain-of-Thought).
    Card lookup takes priority over string triggers; falls back to heuristic triggers.

    Args:
        model_name: Name of the model

    Returns:
        bool: True if it is a reasoning model
    """
    card_result = is_reasoning_model_from_card(model_name)
    if card_result is not None:
        return card_result
    triggers = ["deepseek-r1", "reasoning", "phi4", "qwq", "o1", "o3", "magistral", "glm-5", "minimax-m2", "gemini-2.5", "kimi-k2"]
    return any(t in model_name.lower() for t in triggers)


def get_model_size_class(model_name: str) -> str:
    """
    Determines the hardware-deployment size class of a model based on its name tag.

    Detects parameter count from Ollama-style tags (e.g. 'qwen3:4b', 'phi3.5:3.8b').
    Tiers reflect real-world RAM requirements at Q4 quantization:

        Nano        ≤ 4B    < 4 GB    Smartphone, Raspberry Pi, autocomplete-only
        Edge        5–9B    4–8 GB    Any laptop, MacBook Air M-Series
        Desktop     10–19B  8–14 GB   MacBook Pro, 14 GB Unified Memory
        Workstation 20–35B  14–24 GB  M4 Pro/Max, RTX 4090, high-end consumer
        Server      36–75B  24–48 GB  Mac Studio, dedicated GPU node
        Frontier    >75B / API-only   Cloud-only, no practical local deployment

    Models without a detectable size tag (commercial APIs, cloud proxies) are
    classified as 'Frontier'.

    Args:
        model_name: Raw model name string (e.g. 'qwen3:4b', 'mistral-large-latest')

    Returns:
        One of: 'Nano', 'Edge', 'Desktop', 'Workstation', 'Server', 'Frontier'
    """
    match = re.search(r":e?(\d+(?:\.\d+)?)[bB]", model_name)
    if match:
        try:
            param_b = float(match.group(1))
            if param_b <= 4.0:
                return "Nano"
            if param_b <= 9.0:
                return "Edge"
            if param_b <= 19.0:
                return "Desktop"
            if param_b <= 35.0:
                return "Workstation"
            if param_b <= 75.0:
                return "Server"
            return "Frontier"
        except ValueError:
            pass
    # No size tag → API-only or very large (commercial model, cloud proxy)
    return "Frontier"


def get_model_identity(full_model_string: str) -> dict[str, Any]:
    """
    Parses a raw API model string and extracts friendly metadata for UI and Judge Context.
    Strips provider repository paths while retaining technical suffixes.
    Extracts tags based on model name substrings to provide additional context.

    Returns:
        dict: {
            "raw": full_model_string,
            "display_name": stripped_name,
            "tags": list_of_tags
        }
    """
    name_lower = full_model_string.lower()

    # Extract identity by stripping everything before the last slash
    display_name = full_model_string.rsplit('/', 1)[-1]

    tags = []

    # Specializations
    if any(x in name_lower for x in ["coder", "-code", "code-"]):
        tags.append("Coder")

    if is_reasoning_model(full_model_string) or any(x in name_lower for x in ["thinking"]):
        tags.append("Thinking")

    if "abliterated" in name_lower:
        tags.append("Uncensored-Abliterated")

    if "dolphin" in name_lower or "uncensored" in name_lower or "hermes" in name_lower:
        tags.append("Uncensored-Finetuned")

    if any(x in name_lower for x in ["instruct", "-it", "chat"]):
        tags.append("Instruct")

    if any(x in name_lower for x in ["preview", "experimental", "-exp"]):
        tags.append("Preview")

    # Agentic Orchestrator: Claude Opus models are designed as multi-agent orchestrators
    if "claude-opus" in name_lower:
        tags.append("Agentic-Orchestrator")

    # Thinking-Optional: Models that support toggleable extended thinking but run in standard mode
    if any(x in name_lower for x in ["qwen3", "gemini-2.5"]):
        tags.append("Thinking-Optional")

    if not tags:
        tags.append("General")

    return {
        "raw": full_model_string,
        "display_name": display_name,
        "tags": tags
    }

def get_model_specialization(model_name: str) -> str:
    """
    Classifies models by their primary training specialization.
    Used for context in Bias-Reviews to apply appropriate leniency.

    Returns: Command separated string of specializations from get_model_identity
    """
    identity = get_model_identity(model_name)
    return ", ".join(identity["tags"])


# ---------------------------------------------------------------------------
# Thinking Probe
# ---------------------------------------------------------------------------

_PROBE_PROMPT = (
    "Solve step by step: A train travels 120 km in 1.5 hours. "
    "What is its average speed in km/h? Show your reasoning."
)
_PROBE_MAX_TOKENS = 512
_THINK_TAGS = ("<think>", "<thinking>", "<thought>")


@dataclass
class ThinkingProbeResult:
    detected: bool
    evidence: str
    confidence: Literal["high", "medium", "low"]


def probe_thinking_model(
    model_id: str,
    provider_key: str,
    config: dict,
) -> ThinkingProbeResult:
    """
    Sends a short reasoning prompt to the model and inspects the response for
    Chain-of-Thought signals.

    Signal hierarchy:
      - high:   <think>/<thinking>/<thought> tags present in response
      - medium: reasoning_tokens metadata > 0
      - medium: response_length / 80 chars > 5 (suspiciously long for a simple calc)
      - low:    no signal found

    detected = True if confidence in ("high", "medium")

    Raises:
        RuntimeError: if the API call fails (used as readiness gate in Card-First hook)
    """
    from utils.llm_client import LLMClient  # local import to avoid circular deps

    logger.info("[ThinkingProbe] Probing %s via %s …", model_id, provider_key)

    client = LLMClient(config)
    try:
        raw = client.query(
            model=model_id,
            prompt=_PROBE_PROMPT,
            provider=provider_key,
            max_tokens=_PROBE_MAX_TOKENS,
        )
    except Exception as exc:
        raise RuntimeError(
            f"ThinkingProbe: API call failed for model '{model_id}': {exc}"
        ) from exc

    reasoning_tokens: int = int(
        (client.last_response_metadata or {}).get("reasoning_tokens") or 0
    )

    # Signal A — explicit think-tags (high confidence)
    if any(tag in raw.lower() for tag in _THINK_TAGS):
        return ThinkingProbeResult(
            detected=True,
            evidence=f"Think-tag found in response (first 200 chars): {raw[:200]}",
            confidence="high",
        )

    # Signal B — provider metadata reports reasoning tokens (medium)
    if reasoning_tokens > 0:
        return ThinkingProbeResult(
            detected=True,
            evidence=f"reasoning_tokens={reasoning_tokens} in provider metadata",
            confidence="medium",
        )

    # No CoT signals detected
    return ThinkingProbeResult(
        detected=False,
        evidence=f"No CoT signals found (A: no think-tags, B: reasoning_tokens=0). Response length: {len(raw)} chars",
        confidence="low",
    )
