"""Version/Hash-Erkennung und Ollama-Modell-Info-Helfer.

Importiert aus ``model_card_io`` für Card-Pfad-Lookups.
"""
import json
import logging
import re
import shutil
import subprocess
from typing import Any

from utils.constants import TIMEOUT_OLLAMA_LIST, TIMEOUT_OLLAMA_VERSION
from utils.model_card_io import _card_path

logger = logging.getLogger(__name__)


def _extract_ollama_id(model_name: str, ollama_output: str) -> str | None:
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


def _version_from_card(model_name: str, provider: str) -> str | None:
    """Liest ``model_version`` aus einer existierenden Card, falls vorhanden."""
    card_path = _card_path(model_name, provider)
    if not card_path.exists():
        return None
    try:
        card_data = json.loads(card_path.read_text(encoding="utf-8"))
        card_version = card_data.get("model_version")
        if card_version and str(card_version).strip():
            return str(card_version).strip()
    except Exception:
        return None
    return None


def _version_from_ollama(model_name: str, is_local_attempt: bool) -> str | None:
    """Versucht, eine Version via lokaler Ollama-CLI zu ermitteln."""
    if not is_local_attempt:
        return None
    local_hash = _get_local_model_hash_version(model_name=model_name)
    if local_hash != "k.A.":
        return local_hash
    return None


def _version_claude(model_name: str) -> str | None:
    if "claude" not in model_name:
        return None
    match = re.search(r"claude-\d+(?:-\w+)?-(202\d{5})", model_name)
    if match:
        return match.group(1)
    if "-4-7" in model_name:
        return "4.7"
    if "-4-6" in model_name:
        return "4.6"
    if "-4-5" in model_name:
        return "4.5"
    if "3-5" in model_name:
        return "3.5"
    if "haiku-20240307" in model_name:
        return "20240307"
    return None


def _version_gpt(model_name: str) -> str | None:
    if "gpt" not in model_name:
        return None
    match = re.search(r"-(202\d{5})$|-(0\d{3})$", model_name)
    if match:
        return match.group(1) or match.group(2)
    if "gpt-5.4" in model_name:
        return "5.4"
    if "gpt-5" in model_name:
        return "5.0"
    if "gpt-4o-mini" in model_name:
        return "2024-07-18"
    if "gpt-4o" in model_name:
        return "2024-05-13"
    return "latest"


def _version_gemini(model_name: str) -> str | None:
    if "gemini" not in model_name:
        return None
    if "3.1" in model_name:
        return "3.1-pro-preview"
    if "3-flash-preview" in model_name:
        return "3-flash-preview"
    if "flash" in model_name:
        return "2.5-flash"
    if "pro" in model_name:
        return "2.5-pro"
    return model_name.split("-")[-1]


def _version_mistral(model_name: str) -> str | None:
    if not any(token in model_name for token in ("mistral", "pixtral", "codestral", "magistral")):
        return None
    # magistral is a distinct reasoning model family — don't match mistral version heuristics
    if "magistral" in model_name:
        return "latest"
    match = re.search(r"-(24\d{2})$", model_name)
    if match:
        return match.group(1)
    if "large" in model_name:
        return "3"   # mistral-large-latest → Mistral Large 3 (open-weights)
    if "small" in model_name:
        return "3"   # mistral-small-latest → Mistral Small 3 (open-weights)
    if "medium" in model_name:
        return "2312"
    return "latest"  # covers -latest suffix (e.g. codestral-latest, magistral-small-latest)


def _version_grok(model_name: str) -> str | None:
    if "grok" not in model_name:
        return None
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


def _version_kimi(model_name: str) -> str | None:
    if "kimi" not in model_name:
        return None
    # Match kimi variants: k2, k2.5, k2-0905, k2-thinking, k2-instruct, k2-dev
    match = re.search(r"kimi-(k[\d\.]+(?:-(?:\d{4}|thinking|instruct|dev))?)", model_name.lower())
    if match:
        return match.group(1)
    return "latest"


def _version_qwen(model_name: str) -> str | None:
    if "qwen" not in model_name.lower():
        return None
    match = re.search(r"qwen(\d+(?:\.\d+)?)-?(\d+b)?", model_name.lower())
    if match:
        version = match.group(1)
        size = match.group(2)
        return f"{version}-{size.upper()}" if size else version
    return "latest"


def _version_glm(model_name: str) -> str | None:
    if "glm" not in model_name.lower():
        return None
    match = re.search(r"glm-(\d+(?:\.\d+)?(?:-[a-z]+)?)", model_name.lower())
    if match:
        return match.group(1)
    return "latest"


def _version_minimax(model_name: str) -> str | None:
    if "minimax" not in model_name.lower():
        return None
    match = re.search(r"minimax-(m[\d\.]+)", model_name.lower())
    if match:
        return match.group(1)
    return "latest"


def _version_llama(model_name: str) -> str | None:
    if "llama" not in model_name.lower():
        return None
    match = re.search(r"llama-?(\d+(?:\.\d+)?)-?(\d+b)?", model_name.lower())
    if match:
        version = match.group(1)
        size = match.group(2)
        if size:
            return f"{version}-{size.upper()}"
        return version
    return "latest"


def _version_lfm(model_name: str) -> str | None:
    if "lfm" not in model_name:
        return None
    return "latest"


def _version_o_series(model_name: str) -> str | None:
    if not ("o4" in model_name or "o1" in model_name or "o3" in model_name):
        return None
    match = re.search(r"o[134](?:-[a-z]+)*-(\d{4}-\d{2}-\d{2})", model_name)
    if match:
        return match.group(1)
    if "o4-mini" in model_name:
        return "4-mini"
    if "o4" in model_name:
        return "4"
    if "o3-mini" in model_name:
        return "2025-01-31"
    if model_name == "o1" or model_name.endswith("/o1"):
        return "2024-12-17"
    return "latest"


def get_model_version(model_name: str, provider: str = "ollama", client=None) -> str:
    """
    Retrieves the uniform version mapping of a model without unpredictable fallback fingerprints.
    """
    _ = client  # API compatibility: kept for unchanged call sites.
    p_lower = str(provider).lower().strip()
    prefix = model_name.split("/")[0].lower() if "/" in model_name else ""

    # Card-First: optional override via `model_version` field in model card
    card_version = _version_from_card(model_name, provider)
    if card_version is not None:
        return card_version

    # Attempt Local Ollama Logic if provider implies local, or no explicit provider is given
    is_local_attempt = (p_lower in {"ollama", "local"} or prefix in {"ollama", "local"} or p_lower == "ollama")

    local_version = _version_from_ollama(model_name, is_local_attempt)
    if local_version is not None:
        return local_version

    # Commercial Model Logic — try each family-specific resolver in order.
    for resolver in (
        _version_claude,
        _version_gpt,
        _version_gemini,
        _version_mistral,
        _version_grok,
        _version_kimi,
        _version_qwen,
        _version_glm,
        _version_minimax,
        _version_llama,
        _version_lfm,
        _version_o_series,
    ):
        result = resolver(model_name)
        if result is not None:
            return result

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
    if "vision" in name_lower:  # noqa: SIM103
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
