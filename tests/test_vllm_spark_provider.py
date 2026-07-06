"""Tests für die vllm_spark-Provider-Trennung (asusGX10 via SSH).

Verifiziert:
- Auto-Registry bindet die Subklasse an genau ihren PROVIDER_NAMES
- Basisklasse registriert sich NICHT selbst
- VllmSparkClient liest ausschließlich die vllm_spark-Config
- _build_server_cmd nutzt ``vllm-start --config <NAME>`` mit der TOML-ID
- gpu-mem wird als Override durchgereicht
- Per-Modell ``config``-Pfad überschreibt die Default-Logik
- 600 s-Default-Timeout ist in der Config-Kaskade verankert
"""
import pytest

from utils.providers.base import BaseProviderClient
from utils.providers.vllm_base import VllmBaseClient
from utils.providers.vllm_spark import VllmSparkClient


# Test-Konstanten (vermeidet PLR2004 Magic-Value-Warnungen).
VLLM_CTX: int = 32768
VLLM_BASE_URL: str = "http://192.168.1.200:4300/v1"
VLLM_API_KEY: str = "sk-local-vllm"
HERMES_OVERRIDE_TIMEOUT: int = 900


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vllm_provider_config():
    """Minimale Config mit vllm_spark-Provider."""
    return {
        "providers": {
            "local": {
                "vllm_spark": {
                    "name": "vLLM (asusGX10)",
                    "api_type": "vllm",
                    "enabled": True,
                    "context_window": VLLM_CTX,
                    "base_url": VLLM_BASE_URL,
                    "api_key": VLLM_API_KEY,
                    "server_start_cmd": (
                        "ssh -o BatchMode=yes -o ConnectTimeout=10 -p 22 "
                        "kay_beissert@asusgx10.local vllm-start"
                    ),
                    "server_stop_cmd": (
                        "ssh -o BatchMode=yes -o ConnectTimeout=10 -p 22 "
                        "kay_beissert@asusgx10.local vllm-stop"
                    ),
                    "server_ready_timeout_sec": 600,
                    "server_ready_poll_sec": 10,
                    "server_ready_probe_timeout_sec": 30,
                    "toml_models_dir": "~/ai/shared/configs/vllm/models/",
                    "models": [
                        {
                            "id": "Qwen3.5-35B-A3B",
                            "name": "Qwen 3.5 35B-A3B (vLLM, FP8)",
                            "config": "Qwen3.5-35B-A3B",
                            "max_tokens": 16384,
                        },
                        {
                            "id": "Gemma-4-31B",
                            "name": "Gemma 4 31B (vLLM)",
                        },
                    ],
                },
            },
        },
    }


# ---------------------------------------------------------------------------
# Auto-Registry
# ---------------------------------------------------------------------------

def test_base_class_has_no_provider_names():
    """VllmBaseClient darf sich nicht selbst registrieren."""
    assert VllmBaseClient.PROVIDER_NAMES == []


def test_subclass_registry_uses_only_own_provider():
    """VllmSparkClient registriert sich nur unter vllm_spark."""
    assert BaseProviderClient._registry["vllm_spark"] is VllmSparkClient


# ---------------------------------------------------------------------------
# Provider-spezifischer Config-Lookup
# ---------------------------------------------------------------------------

def test_spark_client_uses_vllm_config(vllm_provider_config):
    """VllmSparkClient liest ausschließlich vllm_spark-Config."""
    client = VllmSparkClient(vllm_provider_config)
    cfg = client._provider_cfg()

    assert cfg["base_url"] == VLLM_BASE_URL
    assert cfg["api_key"] == VLLM_API_KEY
    assert cfg["context_window"] == VLLM_CTX
    assert cfg["api_type"] == "vllm"
    assert client._PROVIDER_KEY == "vllm_spark"


def test_default_port_is_4300():
    """Default-Port ist 4300/v1 (per Spec)."""
    from utils.providers.vllm_base import DEFAULT_VLLM_PORT
    assert DEFAULT_VLLM_PORT == 4300  # noqa: PLR2004 — SSoT-Konstante muss diesen Wert haben


# ---------------------------------------------------------------------------
# Server-Cmd-Bau: --config <TOML-Name>
# ---------------------------------------------------------------------------

def test_build_server_cmd_uses_toml_name(vllm_provider_config):
    """vllm-start wird mit --config <MODELL_ID> aufgerufen."""
    client = VllmSparkClient(vllm_provider_config)
    cmd = client._build_server_cmd("Qwen3.5-35B-A3B")

    # SSH-Wrapper bleibt intakt
    assert cmd.startswith(
        "ssh -o BatchMode=yes -o ConnectTimeout=10 -p 22 "
        "kay_beissert@asusgx10.local vllm-start"
    )
    # --config mit der TOML-ID (ohne .toml)
    assert "--config Qwen3.5-35B-A3B" in cmd


def test_build_server_cmd_honors_explicit_config_path(vllm_provider_config):
    """model_cfg.config überschreibt die model_id-Ableitung."""
    client = VllmSparkClient(vllm_provider_config)
    cmd = client._build_server_cmd("Gemma-4-31B")

    # Gemma-4-31B hat kein explizites ``config`` → model_id wird genutzt
    assert "--config Gemma-4-31B" in cmd


def test_build_server_cmd_with_per_model_gpu_mem(vllm_provider_config):
    """Per-Modell gpu_mem-Override wird durchgereicht."""
    vllm_provider_config["providers"]["local"]["vllm_spark"]["models"][0][
        "gpu_mem_utilization"
    ] = 0.50
    client = VllmSparkClient(vllm_provider_config)
    cmd = client._build_server_cmd("Qwen3.5-35B-A3B")

    assert "--gpu-mem 0.5" in cmd


def test_build_server_cmd_with_provider_default_gpu_mem(vllm_provider_config):
    """Provider-Default gpu_mem wird genutzt wenn kein Per-Modell-Override."""
    vllm_provider_config["providers"]["local"]["vllm_spark"][
        "gpu_mem_utilization"
    ] = 0.85
    client = VllmSparkClient(vllm_provider_config)
    cmd = client._build_server_cmd("Gemma-4-31B")

    assert "--gpu-mem 0.85" in cmd


def test_build_server_cmd_omits_gpu_mem_when_unset(vllm_provider_config):
    """Ohne gpu_mem-Konfig erscheint kein --gpu-mem-Flag."""
    client = VllmSparkClient(vllm_provider_config)
    cmd = client._build_server_cmd("Qwen3.5-35B-A3B")

    assert "--gpu-mem" not in cmd


# ---------------------------------------------------------------------------
# 600 s-Default-Timeout für Modell-Loading
# ---------------------------------------------------------------------------

def test_default_ready_timeout_is_600_seconds():
    """Default-Wert für server_ready_timeout_sec ist 600 (10 Min) — großer MoE-Modelle."""
    from utils.providers.vllm_base import DEFAULT_READY_TIMEOUT_SEC
    assert DEFAULT_READY_TIMEOUT_SEC == 600  # noqa: PLR2004 — SSoT-Konstante ist genau dieser Wert


def test_per_model_ready_timeout_overrides_provider_default(vllm_provider_config):
    """Per-Modell server_ready_timeout_sec überschreibt den Provider-Default."""
    vllm_provider_config["providers"]["local"]["vllm_spark"]["models"][0][
        "server_ready_timeout_sec"
    ] = HERMES_OVERRIDE_TIMEOUT
    client = VllmSparkClient(vllm_provider_config)
    cfg = client._model_cfg("Qwen3.5-35B-A3B")
    assert cfg.get("server_ready_timeout_sec") == HERMES_OVERRIDE_TIMEOUT


# ---------------------------------------------------------------------------
# TOML-Auto-Discovery-Helper
# ---------------------------------------------------------------------------

def test_toml_models_dir_default():
    """Default-TOML-Verzeichnis ist ~/ai/shared/configs/vllm/models/."""
    client = VllmSparkClient({"providers": {"local": {}}})
    assert client._toml_models_dir() == "~/ai/shared/configs/vllm/models/"


def test_discover_remote_tomls_returns_empty_for_non_ssh(vllm_provider_config):
    """Ohne SSH-Wrapper gibt _discover_remote_tomls() eine leere Liste zurück."""
    vllm_provider_config["providers"]["local"]["vllm_spark"][
        "server_start_cmd"
    ] = "vllm-start"
    client = VllmSparkClient(vllm_provider_config)
    assert client._discover_remote_tomls() == []


# ---------------------------------------------------------------------------
# Lookup-Korrektheit bei kanonisierter model_id
# ---------------------------------------------------------------------------

def test_model_cfg_lookup_with_canonical_id(vllm_provider_config):
    """resolve_canonical_model_id kanonisiert Punkte/Bindestriche;
    der Lookup muss die rohe Config-ID trotzdem finden."""
    # Manuelle Kanonisierung: "qwen3.5-35b-a3b" → "qwen3_5-35b-a3b"
    canonical = "qwen3_5-35b-a3b"
    client = VllmSparkClient(vllm_provider_config)
    cfg = client._model_cfg(canonical)

    assert cfg.get("name") == "Qwen 3.5 35B-A3B (vLLM, FP8)"
    assert cfg.get("config") == "Qwen3.5-35B-A3B"
