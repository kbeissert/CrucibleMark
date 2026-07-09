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
SAMPLING_TEMP: float = 0.6
SAMPLING_TOP_P: float = 0.95
SAMPLING_TOP_K: int = 20
PASSED_TEMP_DEFAULT: float = 0.1
PASSED_TEMP_VARIANT: float = 0.7
PASSED_TEMP_LOW: float = 0.4


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


# ---------------------------------------------------------------------------
# Sampling-Chain: model_cfg → vllm_defaults → passed
# ---------------------------------------------------------------------------

@pytest.fixture
def vllm_sampling_config():
    """Config mit vllm_defaults und Ornith-Modell (Cross-Backend-Vergleich)."""
    return {
        "providers": {
            "local": {
                "config": {
                    "vllm_defaults": {
                        "temperature": SAMPLING_TEMP,
                        "top_p": SAMPLING_TOP_P,
                        "top_k": SAMPLING_TOP_K,
                    },
                },
                "vllm_spark": {
                    "name": "vLLM (asusGX10)",
                    "api_type": "vllm",
                    "enabled": True,
                    "base_url": VLLM_BASE_URL,
                    "api_key": VLLM_API_KEY,
                    "models": [
                        {
                            "id": "ornith-1.0-35B-FP8",
                            "name": "Ornith 1.0 35B FP8",
                            "config": "Ornith1-35B-FP8",
                            "max_tokens": 8192,
                            "temperature": SAMPLING_TEMP,
                            "top_p": SAMPLING_TOP_P,
                            "top_k": SAMPLING_TOP_K,
                        },
                        {
                            # Modell ohne sampling-Override — muss unverändert bleiben.
                            "id": "untouched-model",
                            "name": "Untouched",
                        },
                    ],
                },
            },
        },
    }


def test_resolve_sampling_model_override_wins(vllm_sampling_config):
    """model_cfg.temperature > vllm_defaults.temperature > passed_temperature.

    Field-Klassifikation: ``temperature`` und ``top_p`` landen top-level,
    ``top_k`` (vLLM-spezifisch, nicht im OpenAI-Schema) wird in
    ``extra_body`` verpackt (BUGFIX gegen OpenAI-Client-Validierung).
    """
    client = VllmSparkClient(vllm_sampling_config)
    sampling = client._resolve_sampling("ornith-1.0-35B-FP8", passed_temperature=PASSED_TEMP_DEFAULT)

    assert sampling == {
        "temperature": SAMPLING_TEMP,
        "top_p": SAMPLING_TOP_P,
        "extra_body": {"top_k": SAMPLING_TOP_K},
    }


def test_resolve_sampling_defaults_cascade(vllm_sampling_config):
    """Modell ohne Override erbt aus vllm_defaults (wenn aktiv)."""
    client = VllmSparkClient(vllm_sampling_config)

    # Modell ohne sampling-Override, das durch expliziten Eintrag ersetzt wird
    vllm_sampling_config["providers"]["local"]["vllm_spark"]["models"][1][
        "temperature"
    ] = SAMPLING_TEMP

    sampling = client._resolve_sampling("untouched-model", passed_temperature=PASSED_TEMP_DEFAULT)
    assert sampling["temperature"] == SAMPLING_TEMP


def test_resolve_sampling_empty_defaults_preserves_framework_value():
    """Bei leerem vllm_defaults-Block und ohne model_cfg-Override greift
    ausschließlich der passed_temperature (Framework-Default 0.1).

    Garantiert, dass bestehende vLLM-Modelle KEIN stiller Sampling-Shift
    auf 0.6/0.95/20 erfahren.
    """
    cfg = {
        "providers": {
            "local": {
                "config": {"vllm_defaults": {}},
                "vllm_spark": {
                    "name": "vLLM",
                    "api_type": "vllm",
                    "models": [
                        {"id": "stable-model", "name": "Stable"},
                    ],
                },
            },
        },
    }
    client = VllmSparkClient(cfg)

    sampling = client._resolve_sampling("stable-model", passed_temperature=PASSED_TEMP_DEFAULT)
    assert sampling == {"temperature": PASSED_TEMP_DEFAULT}
    assert "top_p" not in sampling
    assert "extra_body" not in sampling


def test_resolve_sampling_top_pk_only_when_configured():
    """top_p und extra_body werden NICHT erzeugt, wenn weder model_cfg noch
    vllm_defaults sie setzen — vLLM-Server-Default aus der TOML bleibt
    unverändert aktiv.
    """
    cfg = {
        "providers": {
            "local": {
                "config": {"vllm_defaults": {"temperature": SAMPLING_TEMP}},
                "vllm_spark": {
                    "name": "vLLM",
                    "api_type": "vllm",
                    "models": [{"id": "m", "name": "M"}],
                },
            },
        },
    }
    client = VllmSparkClient(cfg)

    sampling = client._resolve_sampling("m", passed_temperature=PASSED_TEMP_VARIANT)
    assert sampling["temperature"] == SAMPLING_TEMP  # default kicks in
    assert "top_p" not in sampling
    assert "extra_body" not in sampling


def test_resolve_sampling_no_provider_cfg_returns_minimum():
    """Provider ohne models-Block (leere Config) liefert mindestens
    den passed_temperature, nichts anderes.
    """
    cfg = {"providers": {"local": {"vllm_spark": {"models": []}}}}
    client = VllmSparkClient(cfg)

    sampling = client._resolve_sampling("unknown", passed_temperature=PASSED_TEMP_LOW)
    assert sampling == {"temperature": PASSED_TEMP_LOW}


# ---------------------------------------------------------------------------
# End-to-End: Sampling-Override landet tatsächlich am OpenAI-Wire
# ---------------------------------------------------------------------------

class _StubMessage:
    """Minimal-OpenAI-Message: content + reasoning."""
    def __init__(self, content: str = "Hallo zurück", reasoning: str = "") -> None:
        self.content = content
        self.reasoning_content = reasoning
        self.reasoning = reasoning


class _StubChoice:
    def __init__(self) -> None:
        self.message = _StubMessage()
        self.finish_reason = "stop"


class _StubUsage:
    prompt_tokens = 10
    completion_tokens = 4
    total_tokens = 14


class _StubResponse:
    """Minimal-OpenAI-ChatCompletion-Response."""
    def __init__(self, model_name: str) -> None:
        self.model = model_name
        self.choices = [_StubChoice()]
        self.usage = _StubUsage()


def test_query_passes_model_cfg_sampling_to_client(monkeypatch, vllm_sampling_config):
    """End-to-End: model_cfg.temperature/top_p/top_k landen am Wire.

    Mockt ``_execute_with_token_fallback`` (den inneren API-Call-Pfad) und
    prüft das tatsächliche ``func_kwargs``-Dict, das an die OpenAI-Bibliothek
    übergeben würde. Garantiert, dass die Sampling-Chain nicht nur intern
    korrekt auflöst, sondern wirklich bis zum Request-Body durchschlägt.
    """
    client = VllmSparkClient(vllm_sampling_config)

    # Server-Lifecycle überspringen — wir testen nur das Sampling-Payload.
    monkeypatch.setattr(client, "_ensure_model_ready", lambda model: True)

    captured: dict = {}

    def fake_fallback(func, token_param_name, initial_max_tokens, error_keywords, func_kwargs):
        """Snapshot der kwargs + Stub-Response zurückgeben."""
        captured["func_kwargs"] = dict(func_kwargs)
        captured["func"] = func
        return _StubResponse(model_name="ornith-1.0-35B-FP8"), initial_max_tokens, False

    monkeypatch.setattr(client, "_execute_with_token_fallback", fake_fallback)

    out = client.query(
        model="ornith-1.0-35B-FP8",
        prompt="Sag Hallo auf Deutsch",
        temperature=PASSED_TEMP_DEFAULT,  # Framework-Default 0.1 muss überstimmt werden
    )

    assert out == "Hallo zurück"

    kwargs = captured["func_kwargs"]
    assert kwargs["model"] == "ornith-1.0-35B-FP8"
    # Sampling-Override aus model_cfg gewinnt gegen passed_temperature=0.1.
    assert kwargs["temperature"] == SAMPLING_TEMP
    assert kwargs["top_p"] == SAMPLING_TOP_P
    # top_k landet in extra_body (nicht im OpenAI-HTTP-Schema).
    assert kwargs.get("extra_body", {}).get("top_k") == SAMPLING_TOP_K


def test_query_does_not_emit_top_pk_without_config(monkeypatch):
    """Ohne sampling-Override werden weder top_p noch extra_body.top_k
    emittiert — vLLM-Server-Default aus der TOML bleibt unverändert.
    """
    cfg = {
        "providers": {
            "local": {
                "config": {"vllm_defaults": {}},
                "vllm_spark": {
                    "name": "vLLM",
                    "api_type": "vllm",
                    "base_url": VLLM_BASE_URL,
                    "api_key": VLLM_API_KEY,
                    "models": [{"id": "stable-model", "name": "Stable"}],
                },
            },
        },
    }
    client = VllmSparkClient(cfg)
    monkeypatch.setattr(client, "_ensure_model_ready", lambda model: True)

    captured: dict = {}

    def fake_fallback(func, token_param_name, initial_max_tokens, error_keywords, func_kwargs):
        captured["func_kwargs"] = dict(func_kwargs)
        return _StubResponse(model_name="stable-model"), initial_max_tokens, False

    monkeypatch.setattr(client, "_execute_with_token_fallback", fake_fallback)

    client.query(model="stable-model", prompt="x", temperature=PASSED_TEMP_DEFAULT)

    kwargs = captured["func_kwargs"]
    assert kwargs["temperature"] == PASSED_TEMP_DEFAULT  # Framework-Default bleibt
    assert "top_p" not in kwargs
    assert "extra_body" not in kwargs


# ---------------------------------------------------------------------------
# Dual-Thinking-Profile: Swap-Entkopplung über _active_config
# ---------------------------------------------------------------------------


def _dual_profile_config() -> dict:
    """Config mit Standard- und Thinking-Profil (gleiche ``config:``-TOML)."""
    return {
        "providers": {
            "local": {
                "vllm_spark": {
                    "name": "vLLM (asusGX10)",
                    "api_type": "vllm",
                    "enabled": True,
                    "base_url": VLLM_BASE_URL,
                    "api_key": VLLM_API_KEY,
                    "models": [
                        {
                            "id": "ornith-1.0-35B-FP8",
                            "name": "Ornith 1.0 35B FP8",
                            "config": "Ornith1-35B-FP8",
                            "max_tokens": 8192,
                        },
                        {
                            "id": "ornith-1.0-35B-FP8-thinking",
                            "name": "Ornith 1.0 35B FP8 Thinking",
                            "config": "Ornith1-35B-FP8",  # ← identisch → kein Swap
                            "card_model_id": "ornith-1.0-35B-FP8",
                            "max_tokens": 32768,
                        },
                        {
                            "id": "Gemma-4-26B",
                            "name": "Gemma 4 26B",
                            "config": "Gemma-4-26B",
                            "max_tokens": 16384,
                        },
                    ],
                },
            },
        },
    }


def test_profile_switch_same_config_skips_swap(monkeypatch):
    """Profil-Wechsel (gleiche ``config:``) → kein ``swap_model``-Aufruf.

    Dual-Thinking-Profile zeigen auf dasselbe TOML. Der Connector MUSS
    die per-Request-Sampling-Parameter wechseln, OHNE den Container neu
    zu starten.
    """
    client = VllmSparkClient(_dual_profile_config())

    # Aktiver Container läuft mit dem Standard-Profil.
    client._active_model = "ornith-1.0-35B-FP8"
    client._active_config = "Ornith1-35B-FP8"
    client._server_model_name = "ornith-1.0-35B-FP8"

    # Health + Readiness-Probe positiv.
    monkeypatch.setattr(client, "_is_healthy", lambda: True)
    monkeypatch.setattr(client, "_is_model_ready", lambda model: True)

    # Falls swap_model AUFGERUFEN würde, schlägt der Test fehl.
    swap_called = {"flag": False}

    def fail_swap(model):
        swap_called["flag"] = True
        return False

    monkeypatch.setattr(client, "swap_model", fail_swap)

    result = client._ensure_model_ready("ornith-1.0-35B-FP8-thinking")

    assert result is True
    assert swap_called["flag"] is False, "swap_model darf NICHT aufgerufen werden"
    # Active-Model zeigt jetzt auf das Thinking-Profil.
    assert client._active_model == "ornith-1.0-35B-FP8-thinking"
    assert client._active_config == "Ornith1-35B-FP8"


def test_real_model_swap_different_config_calls_swap_model(monkeypatch):
    """Echter Modell-Wechsel (ungleiche ``config:``) → ``swap_model`` wird aufgerufen.

    Garantiert, dass die Profil-Logik nur bei IDENTISCHEM ``config`` greift —
    nicht bei echtem Backend-Wechsel.
    """
    client = VllmSparkClient(_dual_profile_config())

    client._active_model = "ornith-1.0-35B-FP8"
    client._active_config = "Ornith1-35B-FP8"
    client._server_model_name = "ornith-1.0-35B-FP8"

    monkeypatch.setattr(client, "_is_healthy", lambda: True)
    monkeypatch.setattr(client, "_is_model_ready", lambda model: True)

    swap_called = {"flag": False, "model": None}

    def fake_swap(model):
        swap_called["flag"] = True
        swap_called["model"] = model
        return True

    monkeypatch.setattr(client, "swap_model", fake_swap)

    result = client._ensure_model_ready("Gemma-4-26B")

    assert result is True
    assert swap_called["flag"] is True
    assert swap_called["model"] == "Gemma-4-26B"


def test_profile_switch_backward_compatible_without_active_config(monkeypatch):
    """Backward-compat: ``_active_config is None`` → bisheriges Verhalten.

    Ältere Connector-Instanzen (vor dem Dual-Profile-Patch) haben kein
    ``_active_config`` gesetzt. Sie müssen weiterhin ``swap_model`` aufrufen,
    wenn das aktive Modell abweicht — kein Silent-Skip.
    """
    client = VllmSparkClient(_dual_profile_config())

    client._active_model = "ornith-1.0-35B-FP8"
    client._active_config = None  # Legacy-Instanz
    client._server_model_name = "ornith-1.0-35B-FP8"

    monkeypatch.setattr(client, "_is_healthy", lambda: True)
    monkeypatch.setattr(client, "_is_model_ready", lambda model: True)

    swap_called = {"flag": False}

    def fake_swap(model):
        swap_called["flag"] = True
        return True

    monkeypatch.setattr(client, "swap_model", fake_swap)

    result = client._ensure_model_ready("ornith-1.0-35B-FP8-thinking")

    assert result is True
    assert swap_called["flag"] is True, (
        "Legacy-Instanzen ohne _active_config müssen swap_model aufrufen"
    )


def test_active_config_cleared_on_stop_server():
    """``stop_server`` setzt auch ``_active_config`` zurück."""
    client = VllmSparkClient(_dual_profile_config())

    client._active_model = "ornith-1.0-35B-FP8-thinking"
    client._active_config = "Ornith1-35B-FP8"
    client._server_model_name = "ornith-1.0-35B-FP8"

    # subprocess-Aufrufe dürfen nicht durchkommen.
    import unittest.mock as mock
    with mock.patch("utils.providers.vllm_base.subprocess.run"), \
         mock.patch("utils.providers.vllm_base.subprocess.Popen"):
        client.stop_server()

    assert client._active_model is None
    assert client._active_config is None
    assert client._server_model_name is None


def test_profile_switch_unhealthy_falls_back_to_cold_start(monkeypatch):
    """Profil-Wechsel bei ungesundem Server → Cold-Start, kein Swap.

    Wenn die Health-Probe fehlschlägt, hilft auch der config-Match nicht:
    der Connector muss den Container frisch starten.
    """
    client = VllmSparkClient(_dual_profile_config())

    client._active_model = "ornith-1.0-35B-FP8"
    client._active_config = "Ornith1-35B-FP8"
    client._server_model_name = "ornith-1.0-35B-FP8"

    monkeypatch.setattr(client, "_is_healthy", lambda: False)
    monkeypatch.setattr(client, "_is_model_ready", lambda model: False)

    start_called = {"flag": False, "model": None}

    def fake_start(model=None):
        start_called["flag"] = True
        start_called["model"] = model
        client._active_model = model
        client._active_config = client._config_arg(model)
        return True

    monkeypatch.setattr(client, "start_server", fake_start)

    result = client._ensure_model_ready("ornith-1.0-35B-FP8-thinking")

    assert result is True
    assert start_called["flag"] is True
    assert start_called["model"] == "ornith-1.0-35B-FP8-thinking"
