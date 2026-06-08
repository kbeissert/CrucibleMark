"""Tests für die Phase-19-llama.cpp-Connector-Trennung (M4 ↔ Spark).

Verifiziert:
- Jede Provider-Instanz hat ihren eigenen Config-Lookup (kein Switch-Bug mehr)
- Auto-Registry bindet jede Subklasse an genau ihre PROVIDER_NAMES
- Basisklasse registriert sich NICHT selbst
- Beide Klassen koexistieren ohne State-Leak
- Aliase `llama_cpp` und `llamacpp_local` sind aus der Registry verschwunden
"""
import pytest

from utils.providers.base import BaseProviderClient
from utils.providers.llamacpp import LlamaCppLocalClient
from utils.providers.llamacpp_base import LlamaCppBaseClient
from utils.providers.llamacpp_spark import LlamaCppSparkClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def two_provider_config():
    """Minimale Config mit M4 + Spark Provider, klar getrennt."""
    return {
        "providers": {
            "local": {
                "config": {
                    "context_window": 32768,
                    "llama_cpp_defaults": {
                        "seed": 42,
                        "temperature": 0.8,
                        "top_p": 0.95,
                        "top_k": 40,
                        "min_p": 0.0,
                        "presence_penalty": 0.0,
                        "repeat_penalty": 1.0,
                    },
                },
                "llamacpp": {
                    "name": "Llama.cpp (MacBook Pro)",
                    "api_type": "llamacpp",
                    "enabled": True,
                    "context_window": 32000,
                    "base_url": "http://127.0.0.1:1235/v1",
                    "api_key": "sk-local-m4",
                    "model_dir": "~/ai/lms/gguf",
                    "server_start_cmd": "~/ai/llama.cpp/build/bin/llama-server",
                    "server_stop_cmd": "pkill -f llama-server",
                    "bind_host": "127.0.0.1",
                    "models": [
                        {"id": "m4-model", "model_file": "m4-model.gguf"},
                    ],
                },
                "llamacpp_spark": {
                    "name": "Llama.cpp (DGX Spark)",
                    "api_type": "llamacpp",
                    "enabled": True,
                    "context_window": 65536,
                    "parallel": 4,             # Provider-Default für Parallelität
                    "base_url": "http://192.168.1.42:1235/v1",
                    "api_key": "sk-local-spark",
                    "model_dir": "/home/kay_beissert/ai/models/llm/gguf",
                    "server_start_cmd": "ssh ... llama-server",
                    "server_stop_cmd": "ssh ... pkill",
                    "bind_host": "0.0.0.0",
                    "models": [
                        {"id": "spark-model", "model_file": "spark-model.gguf"},
                    ],
                },
            },
        },
    }


# ---------------------------------------------------------------------------
# Auto-Registry
# ---------------------------------------------------------------------------

def test_base_class_has_no_provider_names():
    """LlamaCppBaseClient darf sich nicht selbst registrieren."""
    assert LlamaCppBaseClient.PROVIDER_NAMES == []
    assert "llamacpp" not in BaseProviderClient._registry.get(LlamaCppBaseClient, {})


def test_subclass_registry_uses_only_own_provider(two_provider_config):
    """Jede Subklasse registriert sich nur unter ihren PROVIDER_NAMES."""
    assert BaseProviderClient._registry["llamacpp"] is LlamaCppLocalClient
    assert BaseProviderClient._registry["llamacpp_spark"] is LlamaCppSparkClient


def test_legacy_aliases_removed_from_registry():
    """Aliase `llama_cpp` und `llamacpp_local` sind aus der Registry verschwunden."""
    assert "llama_cpp" not in BaseProviderClient._registry
    assert "llamacpp_local" not in BaseProviderClient._registry


# ---------------------------------------------------------------------------
# Provider-spezifischer Config-Lookup
# ---------------------------------------------------------------------------

M4_CTX = 32000
SPARK_CTX = 65536


def test_local_client_uses_macbook_config(two_provider_config):
    """LlamaCppLocalClient liest ausschließlich M4-Config."""
    client = LlamaCppLocalClient(two_provider_config)
    cfg = client._provider_cfg()

    assert cfg["base_url"] == "http://127.0.0.1:1235/v1"
    assert cfg["bind_host"] == "127.0.0.1"
    assert cfg["context_window"] == M4_CTX
    assert cfg["api_key"] == "sk-local-m4"
    assert client._PROVIDER_KEY == "llamacpp"


def test_spark_client_uses_spark_config(two_provider_config):
    """LlamaCppSparkClient liest ausschließlich Spark-Config."""
    client = LlamaCppSparkClient(two_provider_config)
    cfg = client._provider_cfg()

    assert cfg["base_url"] == "http://192.168.1.42:1235/v1"
    assert cfg["bind_host"] == "0.0.0.0"
    assert cfg["context_window"] == SPARK_CTX
    assert cfg["api_key"] == "sk-local-spark"
    assert client._PROVIDER_KEY == "llamacpp_spark"


# ---------------------------------------------------------------------------
# Isolierte Instanzen
# ---------------------------------------------------------------------------

def test_both_clients_can_coexist(two_provider_config):
    """Beide Clients koexistieren ohne State-Leak zwischen den Instanzen."""
    local = LlamaCppLocalClient(two_provider_config)
    spark = LlamaCppSparkClient(two_provider_config)

    # Jeder Client nutzt seine eigene base_url
    assert local._base_url() == "http://127.0.0.1:1235/v1"
    assert spark._base_url() == "http://192.168.1.42:1235/v1"

    # _active_model getrennt (eigener State pro Instanz)
    local._active_model = "m4-model"
    assert spark._active_model is None

    # _server_pid getrennt
    local._server_pid = 12345
    assert spark._server_pid is None


def test_no_runtime_provider_switch_attribute():
    """_set_provider_context ist aus der Basisklasse entfernt (Bug-Klasse weg)."""
    assert not hasattr(LlamaCppBaseClient, "_set_provider_context")
    assert not hasattr(LlamaCppLocalClient, "_set_provider_context")
    assert not hasattr(LlamaCppSparkClient, "_set_provider_context")


# ---------------------------------------------------------------------------
# Konstruktor-Validierung
# ---------------------------------------------------------------------------

def test_base_class_cannot_be_instantiated_without_provider_key():
    """Direkte Instanziierung der Basisklasse wirft NotImplementedError."""
    with pytest.raises(NotImplementedError, match="_PROVIDER_KEY"):
        LlamaCppBaseClient({})


# ---------------------------------------------------------------------------
# Defense-in-Depth: _model_cfg() mit kanonisierter ID (resolve_canonical_model_id)
# ---------------------------------------------------------------------------

def test_model_cfg_finds_dotted_id_via_canonical_form():
    """Kanonisierte ID (Punkte→Underscores) muss Config-Eintrag finden.

    Hintergrund: ``resolve_canonical_model_id()`` läuft früh im Entry-Point
    und liefert die kanonisierte Schreibweise (z. B. ``qwen3_5-35b-a3b-q8``).
    Die Config-ID nutzt aber die rohe Schreibweise (``qwen3.5-35b-a3b-q8``).
    Ohne Defense-in-Depth schlägt der Lookup leer und der Server-Start wirft
    ``no model_file configured for model 'qwen3_5-35b-a3b-q8'``.
    """
    config = {
        "providers": {
            "local": {
                "llamacpp_spark": {
                    "base_url": "http://192.168.1.191:1235/v1",
                    "model_dir": "/home/kay_beissert/ai/models/llm/gguf",
                    "models": [
                        {
                            "id": "qwen3.5-35b-a3b-q8",
                            "model_file": "Qwen3.5-35B-A3B-UD-Q8_K_XL.gguf",
                        },
                    ],
                },
            },
        },
    }
    client = LlamaCppSparkClient(config)

    # Exakte Form (wie in der Config)
    cfg_dotted = client._model_cfg("qwen3.5-35b-a3b-q8")
    assert cfg_dotted["model_file"] == "Qwen3.5-35B-A3B-UD-Q8_K_XL.gguf"

    # Kanonisierte Form (wie resolve_canonical_model_id() sie liefert)
    cfg_canonical = client._model_cfg("qwen3_5-35b-a3b-q8")
    assert cfg_canonical["model_file"] == "Qwen3.5-35B-A3B-UD-Q8_K_XL.gguf"

    # Beide liefern dasselbe model_file
    assert cfg_dotted == cfg_canonical


def test_model_cfg_returns_empty_for_unknown_id():
    """Unbekannte ID (auch in kanonisierter Form) liefert leeren Dict."""
    config = {
        "providers": {
            "local": {
                "llamacpp_spark": {
                    "base_url": "http://192.168.1.191:1235/v1",
                    "models": [
                        {"id": "qwen3.5-35b-a3b-q8", "model_file": "x.gguf"},
                    ],
                },
            },
        },
    }
    client = LlamaCppSparkClient(config)
    assert client._model_cfg("unknown-model") == {}
    assert client._model_cfg("qwen3_5-99b-a9b-q9") == {}


# ---------------------------------------------------------------------------
# llm_client._LOCAL_PROVIDERS
# ---------------------------------------------------------------------------

def test_local_providers_tuple_cleaned():
    """llm_client._LOCAL_PROVIDERS enthält keine Aliase mehr."""
    from utils.llm_client import LLMClient

    assert "ollama" in LLMClient._LOCAL_PROVIDERS
    assert "llamacpp" in LLMClient._LOCAL_PROVIDERS
    assert "llamacpp_spark" in LLMClient._LOCAL_PROVIDERS
    assert "llama_cpp" not in LLMClient._LOCAL_PROVIDERS
    assert "llamacpp_local" not in LLMClient._LOCAL_PROVIDERS


# ---------------------------------------------------------------------------
# model_discovery
# ---------------------------------------------------------------------------

def test_discover_local_models_includes_spark(two_provider_config):
    """model_discovery iteriert über alle llamacpp-Provider, nicht nur 'llamacpp'."""
    from scripts.core.model_discovery import discover_local_models

    models = discover_local_models(two_provider_config)

    assert "m4-model" in models
    assert "spark-model" in models


# ---------------------------------------------------------------------------
# llama_cpp_defaults: Server-Start-Flags aus providers.local.config
# ---------------------------------------------------------------------------

def test_build_server_cmd_uses_llama_cpp_defaults(two_provider_config):
    """Bei Modellen ohne Override müssen die llama_cpp_defaults als Flags greifen.

    Verifiziert, dass alle sieben llama.cpp-Defaults (seed, temperature, top_p,
    top_k, min_p, presence_penalty, repeat_penalty) im gebauten Server-Cmd
    landen — mit den SSoT-Werten aus der Config.
    """
    client = LlamaCppLocalClient(two_provider_config)
    cmd = client._build_server_cmd("m4-model")

    assert "--seed 42" in cmd
    assert "--temp 0.8" in cmd
    assert "--top-p 0.95" in cmd
    assert "--top-k 40" in cmd
    assert "--min-p 0.0" in cmd
    assert "--presence-penalty 0.0" in cmd
    assert "--repeat-penalty 1.0" in cmd


# ---------------------------------------------------------------------------
# Per-Modell-Override für context_length + parallel (Hermes-Fall)
# ---------------------------------------------------------------------------

def test_per_model_context_length_and_parallel_override(two_provider_config):
    """Per-Modell-Override für `context_length` und `parallel` greift im Server-Cmd.

    Regression-Test für Hermes 4.3 36B (Hybrid-Attention + SWA-Re-Processings):
    Ein einzelnes Modell soll beim Server-Start andere Flags bekommen als der
    Provider-Default, ohne dass die anderen Modelle desselben Providers
    beeinflusst werden. Früher war `parallel` hartcodiert Provider-Level und
    nicht überschreibbar; jetzt liest `_build_server_cmd()` zuerst `model_cfg`.
    """
    config = two_provider_config
    # Hermes-Override: hermes-spezifische Werte aus dem Fixture ableiten, damit
    # SSoT gewahrt bleibt. Die Override-Werte (16384, 1) sind Hermes-spezifisch
    # und kommen aus der Diagnose (siehe Kommentar beim Hermes-Config-Eintrag).
    hermes_ctx = 16384
    hermes_parallel = 1
    spark_parallel_default = config["providers"]["local"]["llamacpp_spark"]["parallel"]

    config["providers"]["local"]["llamacpp_spark"]["models"] = [
        {
            "id": "hermes-test",
            "model_file": "hermes.gguf",
            "context_length": hermes_ctx,
            "parallel": hermes_parallel,
        },
        {
            "id": "default-model",     # kein Override — nutzt Provider-Default
            "model_file": "default.gguf",
        },
    ]
    client = LlamaCppSparkClient(config)

    hermes_cmd = client._build_server_cmd("hermes-test")
    default_cmd = client._build_server_cmd("default-model")

    # Hermes: Per-Modell-Override greift
    assert f"--ctx-size {hermes_ctx}" in hermes_cmd
    assert f"--parallel {hermes_parallel}" in hermes_cmd
    # Hermes darf NICHT die Provider-Defaults benutzen
    assert f"--ctx-size {SPARK_CTX}" not in hermes_cmd
    assert f"--parallel {spark_parallel_default}" not in hermes_cmd

    # Default-Modell: Provider-Defaults greifen unverändert
    assert f"--ctx-size {SPARK_CTX}" in default_cmd
    assert f"--parallel {spark_parallel_default}" in default_cmd
    # Default-Modell darf NICHT die Hermes-Werte übernehmen
    assert f"--ctx-size {hermes_ctx}" not in default_cmd
    assert f"--parallel {hermes_parallel}" not in default_cmd


def test_per_model_context_length_falls_back_to_provider_default(two_provider_config):
    """Fehlt der `context_length`-Override im model_cfg, gilt der Provider-Default.

    Sicherstellt, dass die neue Override-Logik die bestehende Fallback-Kette
    (Model → Provider → Global → Hardcoded) nicht bricht.
    """
    client = LlamaCppLocalClient(two_provider_config)
    cmd = client._build_server_cmd("m4-model")

    # Provider-Default für llamacpp (M4) aus dem Fixture
    assert f"--ctx-size {M4_CTX}" in cmd
    # Genau ein --ctx-size-Flag im Cmd (kein doppelter Fallback)
    assert cmd.count("--ctx-size") == 1


def test_build_server_cmd_model_override_wins(two_provider_config):
    """Pro-Modell-Override in model_cfg überschreibt jeden llama_cpp_default.

    Setzt für ``m4-model`` sieben eigene Werte und prüft, dass jeder
    entsprechende Flag mit dem Override-Wert (nicht dem Default) gesetzt wird.
    """
    config = two_provider_config
    config["providers"]["local"]["llamacpp"]["models"] = [
        {
            "id": "m4-model",
            "model_file": "m4-model.gguf",
            "temperature": 0.3,
            "top_p": 0.9,
            "top_k": 20,
            "min_p": 0.05,
            "presence_penalty": 0.1,
            "repeat_penalty": 1.05,
        },
    ]
    client = LlamaCppLocalClient(config)
    cmd = client._build_server_cmd("m4-model")

    assert "--temp 0.3" in cmd
    assert "--top-p 0.9" in cmd
    assert "--top-k 20" in cmd
    assert "--min-p 0.05" in cmd
    assert "--presence-penalty 0.1" in cmd
    assert "--repeat-penalty 1.05" in cmd
    # Default-Werte dürfen NICHT im Cmd auftauchen
    assert "--temp 0.8" not in cmd
    assert "--top-p 0.95" not in cmd


def test_build_server_cmd_works_without_defaults_block(two_provider_config):
    """Fehlt der llama_cpp_defaults-Block, greifen hardcoded Code-Defaults.

    Der Code in ``_build_server_cmd()`` hat eigene Fallback-Werte (0.8, 0.95,
    40, 0.0, 0.0, 1.0, 42) für den Fall, dass die Config kein
    ``llama_cpp_defaults`` mitliefert. Damit bleibt die Funktion
    backward-kompatibel zu minimalen Test-Fixtures.
    """
    config = {
        "providers": {
            "local": {
                "llamacpp": {
                    "base_url": "http://127.0.0.1:1235/v1",
                    "model_dir": "/tmp",
                    "server_start_cmd": "llama-server",
                    "bind_host": "127.0.0.1",
                    "models": [
                        {"id": "m", "model_file": "m.gguf"},
                    ],
                },
            },
        },
    }
    client = LlamaCppLocalClient(config)
    cmd = client._build_server_cmd("m")

    assert "--seed 42" in cmd
    assert "--temp 0.8" in cmd
    assert "--top-p 0.95" in cmd
    assert "--top-k 40" in cmd
    assert "--min-p 0.0" in cmd
    assert "--presence-penalty 0.0" in cmd
    assert "--repeat-penalty 1.0" in cmd
