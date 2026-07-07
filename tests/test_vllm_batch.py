"""Tests für scripts/core/vllm_batch.py — Provider-Discovery & Lifecycle.

Abdeckung:
- is_vllm_provider: True / False-Varianten, Edge-Case None
- get_enabled_vllm_providers: leere Config, aktivierter Provider,
  api_type-Diskriminierung (llamacpp wird ausgeschlossen), enabled=false
- stop_vllm_provider_server: dedupliziert server_stop_cmd, no-op bei leerem
  String, beendet früh wenn kein Provider aktiv
- run_vllm_provider_cleanup: post_stop_cmd wird ausgeführt,
  cleanup_on_exit=false überspringt
- vllm_provider_session: Session-Erfolg mit Mock-Client, Exception-Pfad
  stoppt trotzdem, fehlender Client wirft VllmSessionError

Hinweis: Die Cache-Helper (get_startable_assets, canonical_lookup_keys,
get_existing_results) bleiben bewusst in scripts/core/llamacpp_batch.py
und werden dort getestet — keine Doppeltestung hier.
"""
import logging
from unittest.mock import patch, MagicMock

import pytest

from scripts.core.vllm_batch import (
    is_vllm_provider,
    get_enabled_vllm_providers,
    set_vllm_provider_context,
    stop_vllm_provider_server,
    run_vllm_provider_cleanup,
    vllm_model_session,
    VllmSessionError,
    VLLM_STOP_SETTLE_SEC,
)


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

def test_vllm_stop_settle_sec_default_is_three():
    """Per CLAUDE.md-Konservativ-Annahme (gleicher Default wie llama.cpp)."""
    assert VLLM_STOP_SETTLE_SEC == 3  # noqa: PLR2004


# ---------------------------------------------------------------------------
# is_vllm_provider
# ---------------------------------------------------------------------------

class TestIsVllmProvider:
    """Provider-Key-Erkennung — Single-Provider heute (vllm_spark)."""

    def test_vllm_spark_is_true(self):
        assert is_vllm_provider("vllm_spark") is True

    def test_legacy_llamacpp_keys_are_false(self):
        assert is_vllm_provider("llamacpp") is False
        assert is_vllm_provider("llamacpp_spark") is False

    def test_other_providers_are_false(self):
        assert is_vllm_provider("ollama") is False
        assert is_vllm_provider("anthropic") is False
        assert is_vllm_provider("mistral") is False

    def test_empty_and_none_safe(self):
        """Edge-Cases: leere Strings / None crashen nicht."""
        assert is_vllm_provider("") is False  # type: ignore[arg-type]
        assert is_vllm_provider(None) is False  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# get_enabled_vllm_providers
# ---------------------------------------------------------------------------

class TestGetEnabledVllmProviders:
    """Discovery analog zu get_enabled_llamacpp_providers."""

    def test_empty_config_returns_empty_list(self):
        assert get_enabled_vllm_providers({}) == []
        assert get_enabled_vllm_providers({"providers": {}}) == []
        assert get_enabled_vllm_providers({"providers": {"local": {}}}) == []

    def test_no_local_section_returns_empty(self):
        cfg = {"providers": {"commercial": {"vllm_spark": {"api_type": "vllm", "enabled": True}}}}
        assert get_enabled_vllm_providers(cfg) == []

    def test_disabled_provider_skipped(self):
        cfg = {
            "providers": {
                "local": {
                    "vllm_spark": {"api_type": "vllm", "enabled": False},
                }
            }
        }
        assert get_enabled_vllm_providers(cfg) == []

    def test_wrong_api_type_skipped(self):
        """api_type=llamacpp darf NICHT in vllm-Liste landen (Diskriminierung)."""
        cfg = {
            "providers": {
                "local": {
                    "llamacpp": {"api_type": "llamacpp", "enabled": True},
                    "llamacpp_spark": {"api_type": "llamacpp", "enabled": True},
                }
            }
        }
        assert get_enabled_vllm_providers(cfg) == []

    def test_enabled_vllm_returned_in_config_order(self):
        cfg = {
            "providers": {
                "local": {
                    "ollama": {"api_type": "ollama", "enabled": True},
                    "vllm_spark": {
                        "api_type": "vllm",
                        "enabled": True,
                        "name": "vLLM (asusGX10)",
                    },
                    "llamacpp": {"api_type": "llamacpp", "enabled": True},
                }
            }
        }
        result = get_enabled_vllm_providers(cfg)
        assert len(result) == 1
        provider_key, provider_cfg = result[0]
        assert provider_key == "vllm_spark"
        assert provider_cfg["name"] == "vLLM (asusGX10)"

    def test_non_dict_value_skipped(self):
        """Robustheit: falsch formatierte Provider-Configs werden ignoriert."""
        cfg = {
            "providers": {
                "local": {
                    "vllm_spark": "this-should-be-a-dict",
                    "llamacpp": {"api_type": "llamacpp", "enabled": True},
                }
            }
        }
        assert get_enabled_vllm_providers(cfg) == []

    def test_unregistered_vllm_key_skipped_with_warning(self, caplog):
        """Config hat api_type=vllm, aber Key nicht in VLLM_PROVIDER_KEYS.

        Fail-Fast: Provider wird übersprungen + Warning geloggt, statt
        silent-breakage in _is_local_server_provider zu riskieren.
        """
        cfg = {
            "providers": {
                "local": {
                    "vllm_future_box": {
                        "api_type": "vllm",
                        "enabled": True,
                    },
                }
            }
        }
        with caplog.at_level(logging.WARNING, logger="scripts.core.vllm_batch"):
            result = get_enabled_vllm_providers(cfg)
        assert result == []
        assert "vllm_future_box" in caplog.text
        assert "VLLM_PROVIDER_KEYS" in caplog.text


# ---------------------------------------------------------------------------
# set_vllm_provider_context
# ---------------------------------------------------------------------------

class TestSetVllmProviderContext:
    """Context-Setter ist tolerant gegen Client ohne _set_provider_context."""

    def test_calls_setter_if_present(self):
        client = MagicMock()
        set_vllm_provider_context(client, "vllm_spark")
        client._set_provider_context.assert_called_once_with("vllm_spark")

    def test_silent_noop_if_setter_missing(self):
        """VllmBaseClient hat heute keinen Setter — Aufruf darf nicht crashen."""
        client = object()  # kein _set_provider_context-Attribut
        # Darf KEINE Exception werfen
        set_vllm_provider_context(client, "vllm_spark")


# ---------------------------------------------------------------------------
# stop_vllm_provider_server
# ---------------------------------------------------------------------------

class TestStopVllmProviderServer:
    """Prophylaktischer Stop analog stop_llamacpp_provider_server."""

    def test_no_providers_noop(self):
        """Ohne aktivierten Provider passiert nichts (silent)."""
        cfg = {"providers": {"local": {}}}
        # Darf keine Exception werfen, kein subprocess-Aufruf
        with patch("scripts.core.vllm_batch.subprocess.run") as mock_run, \
             patch("scripts.core.vllm_batch.time.sleep") as mock_sleep:
            stop_vllm_provider_server(cfg)
        mock_run.assert_not_called()
        mock_sleep.assert_not_called()

    def test_specific_provider_key_filters_list(self):
        """Bei provider_key-Filter läuft nur das angefragte stop_cmd."""
        cfg = {
            "providers": {
                "local": {
                    "vllm_spark": {
                        "api_type": "vllm",
                        "enabled": True,
                        "server_stop_cmd": "vllm-stop-spark",
                    },
                }
            }
        }
        with patch("scripts.core.vllm_batch.subprocess.run") as mock_run, \
             patch("scripts.core.vllm_batch.time.sleep"):
            stop_vllm_provider_server(cfg, provider_key="vllm_spark")
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        assert "vllm-stop-spark" in args[0]

    def test_provider_key_filter_excludes_other_providers(self):
        """provider_key-Filter stoppt NUR den angefragten Provider."""
        cfg = {
            "providers": {
                "local": {
                    "vllm_spark": {
                        "api_type": "vllm",
                        "enabled": True,
                        "server_stop_cmd": "vllm-stop-spark",
                    },
                    "vllm_box2": {
                        "api_type": "vllm",
                        "enabled": True,
                        "server_stop_cmd": "vllm-stop-box2",
                    },
                }
            }
        }
        with patch("scripts.core.vllm_batch.VLLM_PROVIDER_KEYS",
                   frozenset({"vllm_spark", "vllm_box2"})), \
             patch("scripts.core.vllm_batch.subprocess.run") as mock_run, \
             patch("scripts.core.vllm_batch.time.sleep"):
            stop_vllm_provider_server(cfg, provider_key="vllm_spark")
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        assert "vllm-stop-spark" in args[0]
        assert "vllm-stop-box2" not in args[0]

    def test_dedupes_stop_commands(self):
        """Zwei Provider mit gleichem stop_cmd → nur 1 subprocess-Aufruf."""
        cfg = {
            "providers": {
                "local": {
                    "vllm_a": {
                        "api_type": "vllm",
                        "enabled": True,
                        "server_stop_cmd": "vllm-stop",
                    },
                    "vllm_b": {
                        "api_type": "vllm",
                        "enabled": True,
                        "server_stop_cmd": "vllm-stop",  # gleich
                    },
                }
            }
        }
        # Test-Keys sind nicht in VLLM_PROVIDER_KEYS registriert → patchen,
        # damit die Validierung in get_enabled_vllm_providers sie durchlässt.
        with patch("scripts.core.vllm_batch.VLLM_PROVIDER_KEYS",
                   frozenset({"vllm_a", "vllm_b"})), \
             patch("scripts.core.vllm_batch.subprocess.run") as mock_run, \
             patch("scripts.core.vllm_batch.time.sleep"):
            stop_vllm_provider_server(cfg)
        assert mock_run.call_count == 1

    def test_empty_stop_cmd_skipped(self):
        cfg = {
            "providers": {
                "local": {
                    "vllm_spark": {
                        "api_type": "vllm",
                        "enabled": True,
                        "server_stop_cmd": "   ",
                    },
                }
            }
        }
        with patch("scripts.core.vllm_batch.subprocess.run") as mock_run, \
             patch("scripts.core.vllm_batch.time.sleep"):
            stop_vllm_provider_server(cfg)
        mock_run.assert_not_called()

    def test_missing_stop_cmd_warns_and_skips(self, caplog):
        """Fehlendes server_stop_cmd → Warning + Skip (kein lokales vllm-stop)."""
        cfg = {
            "providers": {
                "local": {
                    "vllm_spark": {
                        "api_type": "vllm",
                        "enabled": True,
                        # server_stop_cmd bewusst weggelassen
                    },
                }
            }
        }
        with caplog.at_level(logging.WARNING, logger="scripts.core.vllm_batch"), \
             patch("scripts.core.vllm_batch.subprocess.run") as mock_run, \
             patch("scripts.core.vllm_batch.time.sleep"):
            stop_vllm_provider_server(cfg)
        mock_run.assert_not_called()
        assert "server_stop_cmd" in caplog.text


# ---------------------------------------------------------------------------
# run_vllm_provider_cleanup
# ---------------------------------------------------------------------------

class TestRunVllmProviderCleanup:
    """End-of-Batch Cleanup-Hook."""

    def test_cleanup_disabled_skips_run(self):
        cfg = {"cleanup_on_exit": False, "server_post_stop_cmd": "rm -rf /tmp/should-not-run"}
        with patch("scripts.core.vllm_batch.subprocess.run") as mock_run:
            run_vllm_provider_cleanup("vllm_spark", cfg)
        mock_run.assert_not_called()

    def test_cleanup_enabled_runs_post_stop_cmd(self):
        cfg = {"cleanup_on_exit": True, "server_post_stop_cmd": "echo cleanup"}
        with patch("scripts.core.vllm_batch.subprocess.run") as mock_run:
            run_vllm_provider_cleanup("vllm_spark", cfg)
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        assert "cleanup" in args[0]

    def test_no_post_stop_cmd_is_noop(self):
        cfg = {"cleanup_on_exit": True}
        with patch("scripts.core.vllm_batch.subprocess.run") as mock_run:
            run_vllm_provider_cleanup("vllm_spark", cfg)
        mock_run.assert_not_called()

    def test_subprocess_exception_swallows_cleanly(self):
        """Cleanup-Fehler dürfen Batch-Abschluss nicht verhindern.

        except Exception (breit) fängt auch unexpected Typen ab — parallel
        zu run_llamacpp_provider_cleanup. Getestet mit OSError als
        realistischem Fall (Shell nicht gefunden).
        """
        cfg = {"cleanup_on_exit": True, "server_post_stop_cmd": "false"}
        with patch(
            "scripts.core.vllm_batch.subprocess.run",
            side_effect=OSError("shell not found"),
        ):
            # Darf NICHT propagieren
            run_vllm_provider_cleanup("vllm_spark", cfg)

    def test_unexpected_exception_also_swallowed(self):
        """Auch unexpected Exceptions (z.B. TypeError) dürfen nicht propagieren.

        Dokumentierte Invariante: 'Cleanup darf den Batch-Abschluss nicht
        verhindern'. except Exception ist bewusst breit (parallel zu llamacpp).
        """
        cfg = {"cleanup_on_exit": True, "server_post_stop_cmd": "false"}
        with patch(
            "scripts.core.vllm_batch.subprocess.run",
            side_effect=TypeError("bad config value"),
        ):
            run_vllm_provider_cleanup("vllm_spark", cfg)


# ---------------------------------------------------------------------------
# vllm_model_session
# ---------------------------------------------------------------------------

class TestVllmModelSession:
    """Context-Manager: Server-Start + guaranteed Stop + Settle."""

    def _make_runner(self, client: MagicMock | None) -> MagicMock:
        runner = MagicMock()
        runner.client.clients.get.return_value = client
        return runner

    def test_session_yields_client_when_start_succeeds(self):
        client = MagicMock()
        client.start_server.return_value = True
        runner = self._make_runner(client)

        with patch("scripts.core.vllm_batch.time.sleep"), \
             vllm_model_session(runner, "vllm_spark", "my-model") as got:
            assert got is client
            client.start_server.assert_called_once_with("my-model")

        client.stop_server.assert_called_once()

    def test_session_stops_even_on_exception(self):
        client = MagicMock()
        client.start_server.return_value = True
        runner = self._make_runner(client)

        with (
            pytest.raises(RuntimeError, match="boom"),
            patch("scripts.core.vllm_batch.time.sleep"),
            vllm_model_session(runner, "vllm_spark", "my-model"),
        ):
            raise RuntimeError("boom")

        client.stop_server.assert_called_once()

    def test_session_raises_if_client_missing(self):
        runner = self._make_runner(None)  # client=None
        with (
            pytest.raises(VllmSessionError, match="nicht im Client-Registry"),
            vllm_model_session(runner, "vllm_spark", "my-model"),
        ):
            pass

    def test_session_raises_if_start_fails(self):
        client = MagicMock()
        client.start_server.return_value = False
        runner = self._make_runner(client)
        with (
            pytest.raises(VllmSessionError, match="konnte nicht gestartet"),
            vllm_model_session(runner, "vllm_spark", "my-model"),
        ):
            pass
        client.stop_server.assert_not_called()

    def test_session_does_not_run_cleanup(self):
        """Session ist reine Server-Lifecycle — Cleanup ist Orchestrator-Verantwortung.

        vllm_model_session darf run_vllm_provider_cleanup NICHT aufrufen
        (sonst läuft post_stop_cmd pro Modell statt pro Batch).
        """
        client = MagicMock()
        client.start_server.return_value = True
        runner = self._make_runner(client)

        with patch("scripts.core.vllm_batch.run_vllm_provider_cleanup") as mock_cleanup, \
             patch("scripts.core.vllm_batch.time.sleep"), \
             vllm_model_session(runner, "vllm_spark", "my-model"):
            pass

        client.stop_server.assert_called_once()
        mock_cleanup.assert_not_called()

    def test_session_settles_after_stop(self):
        """Session wartet VLLM_STOP_SETTLE_SEC nach stop_server (Port-Release)."""
        client = MagicMock()
        client.start_server.return_value = True
        runner = self._make_runner(client)

        with patch("scripts.core.vllm_batch.time.sleep") as mock_sleep, \
             vllm_model_session(runner, "vllm_spark", "my-model"):
            pass

        client.stop_server.assert_called_once()
        mock_sleep.assert_called_once_with(VLLM_STOP_SETTLE_SEC)
