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


# ---------------------------------------------------------------------------
# Pre-Flight-Check: model_file-Existenz (Pitfall-Diagnose 2026-06-10)
# ---------------------------------------------------------------------------

def test_preflight_check_passes_when_model_file_exists(tmp_path):
    """Wenn die model_file auf der Disk existiert, gibt der Check True zurück.

    Regression-Test für Pitfall-Diagnose 2026-06-10: ``gemma-4-12b-it-ud-q4_k_xl``
    lief 180s in Timeout, weil ``model_file`` auf eine nicht-existente Datei
    zeigte. Mit dem Pre-Flight-Check wird dieser Fail in <1s sichtbar.
    """
    real_gguf = tmp_path / "real-model.gguf"
    real_gguf.write_bytes(b"\x00")  # Existenz reicht für den Check

    config = {
        "providers": {
            "local": {
                "llamacpp": {
                    "base_url": "http://127.0.0.1:1235/v1",
                    "model_dir": str(tmp_path),
                    "server_start_cmd": "llama-server",
                    "bind_host": "127.0.0.1",
                    "models": [
                        {"id": "real-model", "model_file": "real-model.gguf"},
                    ],
                },
            },
        },
    }
    client = LlamaCppLocalClient(config)
    ok, err = client._preflight_check_model_file("real-model")

    assert ok is True
    assert err == ""


def test_preflight_check_fails_when_model_file_missing(tmp_path):
    """Tippfehler im model_file (Pitfall 2026-06-10): Check muss fehlschlagen.

    Bei ``gemma-4-12b-it-ud-q4_k_xl`` war in der Config ``...-UD-Q4_K_X.gguf``
    (ohne ``L``) eingetragen, die Datei hieß aber ``...-UD-Q4_K_XL.gguf``.
    Der Server lief 180s in Timeout. Mit dem Pre-Flight-Check wird der Fail
    in <1s sichtbar — Check gibt False zurück mit klarer Fehlermeldung, die
    den konfigurierten Pfad UND den Provider-Key enthält.
    """
    config = {
        "providers": {
            "local": {
                "llamacpp": {
                    "base_url": "http://127.0.0.1:1235/v1",
                    "model_dir": str(tmp_path),
                    "server_start_cmd": "llama-server",
                    "bind_host": "127.0.0.1",
                    "models": [
                        # Tippfehler: UD-Q4_K_X statt UD-Q4_K_XL
                        {"id": "gemma-4-12b-it-ud-q4_k_xl",
                         "model_file": "gemma-4-12b-it-UD-Q4_K_X.gguf"},
                    ],
                },
            },
        },
    }
    client = LlamaCppLocalClient(config)
    ok, err = client._preflight_check_model_file("gemma-4-12b-it-ud-q4_k_xl")

    assert ok is False
    # Fehlermeldung muss den Pfad UND den Provider-Key nennen,
    # damit Operator sofort weiß, wo zu suchen ist.
    assert "gemma-4-12b-it-UD-Q4_K_X.gguf" in err
    assert "gemma-4-12b-it-ud-q4_k_xl" in err
    assert "llamacpp" in err  # Provider-Key in der Hinweis-Zeile


def test_preflight_check_fails_when_model_file_empty(tmp_path):
    """Fehlt der model_file-Eintrag in der Config, wirft _resolve_model_path.

    ``_preflight_check_model_file`` fängt die ValueError-Variante ab und
    liefert (False, fehlermeldung) — damit ``start_server()`` keinen
    Server-Start versucht.
    """
    config = {
        "providers": {
            "local": {
                "llamacpp": {
                    "base_url": "http://127.0.0.1:1235/v1",
                    "model_dir": str(tmp_path),
                    "server_start_cmd": "llama-server",
                    "bind_host": "127.0.0.1",
                    "models": [
                        {"id": "no-file-model", "model_file": ""},
                    ],
                },
            },
        },
    }
    client = LlamaCppLocalClient(config)
    ok, err = client._preflight_check_model_file("no-file-model")

    assert ok is False
    assert "no model_file configured" in err


def test_preflight_check_skipped_for_remote_ssh_provider(tmp_path):
    """Remote-Provider (SSH) überspringen den lokalen Datei-Check.

    ``_preflight_check_model_file()`` gibt ``(True, '')`` zurück, wenn
    ``server_start_cmd`` mit ``ssh`` beginnt — unabhängig davon, ob die
    Datei lokal existiert. Der Pfad liegt auf der Remote-Maschine und ist
    vom Benchmark-Host nicht erreichbar.

    Pitfall-Diagnose 2026-06-10: llamacpp_spark scheiterte immer am
    Preflight, weil ``Path.is_file()`` den Linux-Pfad auf macOS prüfte.
    """
    config = {
        "providers": {
            "local": {
                "llamacpp_spark": {
                    "base_url": "http://192.168.1.191:1235/v1",
                    "model_dir": str(tmp_path),
                    "server_start_cmd": "ssh -p 22 user@host llama-server",
                    "bind_host": "0.0.0.0",
                    "models": [
                        {"id": "spark-missing",
                         "model_file": "does-not-exist.gguf"},
                    ],
                },
            },
        },
    }
    client = LlamaCppSparkClient(config)
    ok, err = client._preflight_check_model_file("spark-missing")

    # Remote-Provider: Check übersprungen → immer (True, "")
    assert ok is True
    assert err == ""


def test_is_remote_provider_ssh_detection():
    """_is_remote_provider() erkennt SSH-basierte Provider korrekt.

    Beginnt ``server_start_cmd`` mit ``ssh``, gilt der Provider als
    Remote — lokale ``Path.is_file()``-Checks werden übersprungen.
    """
    ssh_config = {
        "providers": {
            "local": {
                "llamacpp_spark": {
                    "server_start_cmd": "ssh -p 22 user@host llama-server",
                    "models": [],
                },
            },
        },
    }
    local_config = {
        "providers": {
            "local": {
                "llamacpp_spark": {
                    "server_start_cmd": "/usr/local/bin/llama-server",
                    "models": [],
                },
            },
        },
    }
    assert LlamaCppSparkClient(ssh_config)._is_remote_provider() is True
    assert LlamaCppSparkClient(local_config)._is_remote_provider() is False


def test_start_server_returns_false_on_preflight_failure_without_popen(tmp_path, monkeypatch):
    """start_server() darf subprocess.Popen NICHT aufrufen, wenn Pre-Flight fehlschlägt.

    Das ist der entscheidende Unterschied: ohne Pre-Flight-Check würde der
    llama-server mit dem falschen Pfad gestartet, 180s warten, dann aufgeben.
    Mit Pre-Flight-Check wird der Fehler in <1s entdeckt — und Popen wird
    NIE aufgerufen (sonst hätten wir genau das Problem, das wir lösen wollen).
    """
    config = {
        "providers": {
            "local": {
                "llamacpp": {
                    "base_url": "http://127.0.0.1:1235/v1",
                    "model_dir": str(tmp_path),
                    "server_start_cmd": "llama-server",
                    "bind_host": "127.0.0.1",
                    "models": [
                        {"id": "missing-model",
                         "model_file": "missing-model.gguf"},
                    ],
                },
            },
        },
    }
    client = LlamaCppLocalClient(config)

    # Popen darf NICHT aufgerufen werden — wir mocken es so, dass ein
    # versehentlicher Aufruf den Test sofort failen lässt.
    popen_calls: list[dict[str, object]] = []
    def fake_popen(*args, **kwargs):  # noqa: ANN001, ANN002, ANN201
        popen_calls.append({"args": args, "kwargs": kwargs})
        raise AssertionError(
            "subprocess.Popen wurde aufgerufen, obwohl Pre-Flight-Check "
            "fehlgeschlagen ist — das ist der Bug, den wir verhindern wollen."
        )

    monkeypatch.setattr(
        "utils.providers.llamacpp_base.subprocess.Popen", fake_popen,
    )

    # Pre-Flight muss fehlschlagen, _is_healthy muss False zurückgeben
    # (sonst landen wir in Pfad 1/2/3, die den Pre-Flight nicht aufrufen).
    monkeypatch.setattr(client, "_is_healthy", lambda: False)
    monkeypatch.setattr(client, "_query_active_model", lambda: None)

    result = client.start_server("missing-model")

    assert result is False
    assert popen_calls == []  # Popen wurde NIE aufgerufen


def test_start_server_proceeds_to_popen_when_preflight_passes(tmp_path, monkeypatch):
    """Bei erfolgreichem Pre-Flight wird Popen aufgerufen (Happy-Path).

    Sicherstellt, dass der Pre-Flight-Check nicht versehentlich den
    Happy-Path blockiert — wenn die Datei existiert, muss der Server-Start
    normal weiterlaufen.
    """
    real_gguf = tmp_path / "ok-model.gguf"
    real_gguf.write_bytes(b"\x00")

    config = {
        "providers": {
            "local": {
                "llamacpp": {
                    "base_url": "http://127.0.0.1:1235/v1",
                    "model_dir": str(tmp_path),
                    "server_start_cmd": "llama-server",
                    "bind_host": "127.0.0.1",
                    "models": [
                        {"id": "ok-model", "model_file": "ok-model.gguf"},
                    ],
                },
            },
        },
    }
    client = LlamaCppLocalClient(config)

    popen_called: dict[str, object] = {}
    def fake_popen(*args, **kwargs):  # noqa: ANN001, ANN002, ANN201
        popen_called["called"] = True
        class FakeProc:
            pid = 99999
        return FakeProc()

    monkeypatch.setattr(
        "utils.providers.llamacpp_base.subprocess.Popen", fake_popen,
    )
    monkeypatch.setattr(client, "_is_healthy", lambda: False)
    monkeypatch.setattr(client, "_query_active_model", lambda: None)
    # Readiness-Loop sofort beenden (sonst 180s Wartezeit)
    monkeypatch.setattr(client, "_wait_for_model_ready", lambda *a, **kw: False)

    result = client.start_server("ok-model")

    assert popen_called.get("called") is True, "Popen wurde nicht aufgerufen"
    assert result is False  # Server wird nicht ready → False
