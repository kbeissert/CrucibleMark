"""
Tests für utils/provider_health.py — Pre-Flight-Checks für untested Cards.

Deckt ab:
    - get_installed_ollama_models()   (Cache, force_refresh, Fehlertoleranz)
    - is_ollama_model_installed()     (normalisiert Präfixe + Doppelpunkte)
    - is_api_provider_available()     (ENV-Var gesetzt/leer)
    - validate_untested_card()        (Ollama/API/llama.cpp/unknown/missing)
    - filter_testable_cards()         (Aufteilung testable/unreachable)
    - _run_untested_tooluse_models()  (Pre-Flight delegiert nur testbare,
                                       schreibt Unreachables-Report)

Mockt subprocess.run + 'ollama list' Output.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_ollama_cache():
    """Setzt den prozess-lokalen Ollama-Cache vor jedem Test zurück."""
    from utils import provider_health
    provider_health._OLLAMA_MODEL_CACHE.value = None
    yield
    provider_health._OLLAMA_MODEL_CACHE.value = None


@pytest.fixture
def ollama_installed_list() -> MagicMock:
    """Mock für 'ollama list' mit drei installierten Modellen."""
    output = "\n".join([
        "NAME                    ID            SIZE      MODIFIED",
        "gemma3:12b              a1b2c3d4e5f6  8.0 GB    2 hours ago",
        "qwen3:32b               f6e5d4c3b2a1  20.0 GB   1 day ago",
        "ministral-3:14b         1234567890ab  9.0 GB    3 hours ago",
    ])
    mock = MagicMock(return_value=MagicMock(
        stdout=output,
        stderr="",
        returncode=0,
    ))
    return mock


# ---------------------------------------------------------------------------
# 1. get_installed_ollama_models
# ---------------------------------------------------------------------------

class TestGetInstalledOllamaModels:
    def test_returns_set_with_installed_names(self, ollama_installed_list: MagicMock) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", ollama_installed_list),
        ):
            from utils.provider_health import get_installed_ollama_models
            result = get_installed_ollama_models()
        assert "gemma3:12b" in result
        assert "qwen3:32b" in result
        assert "ministral-3:14b" in result
        assert len(result) == 3

    def test_caches_result(self, ollama_installed_list: MagicMock) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", ollama_installed_list) as m,
        ):
            from utils.provider_health import get_installed_ollama_models
            get_installed_ollama_models()
            get_installed_ollama_models()
            get_installed_ollama_models()
        # subprocess.run wird nur EINMAL aufgerufen (danach Cache)
        assert m.call_count == 1

    def test_force_refresh_reruns(self, ollama_installed_list: MagicMock) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", ollama_installed_list) as m,
        ):
            from utils.provider_health import get_installed_ollama_models
            get_installed_ollama_models()
            get_installed_ollama_models(force_refresh=True)
        assert m.call_count == 2

    def test_missing_binary_returns_empty(self) -> None:
        with patch("shutil.which", return_value=None):
            from utils.provider_health import get_installed_ollama_models
            result = get_installed_ollama_models()
        assert result == set()

    def test_timeout_returns_empty(self) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ollama", timeout=5)),
        ):
            from utils.provider_health import get_installed_ollama_models
            result = get_installed_ollama_models()
        assert result == set()


# ---------------------------------------------------------------------------
# 2. is_ollama_model_installed
# ---------------------------------------------------------------------------

class TestIsOllamaModelInstalled:
    def test_installed_model(self, ollama_installed_list: MagicMock) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", ollama_installed_list),
        ):
            from utils.provider_health import is_ollama_model_installed
            assert is_ollama_model_installed("gemma3:12b") is True

    def test_not_installed_model(self, ollama_installed_list: MagicMock) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", ollama_installed_list),
        ):
            from utils.provider_health import is_ollama_model_installed
            assert is_ollama_model_installed("qwen2.5vl:7b") is False

    def test_strips_ollama_prefix(self, ollama_installed_list: MagicMock) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", ollama_installed_list),
        ):
            from utils.provider_health import is_ollama_model_installed
            # 'ollama/gemma3:12b' muss als 'gemma3:12b' erkannt werden
            assert is_ollama_model_installed("ollama/gemma3:12b") is True

    def test_empty_string_returns_false(self) -> None:
        from utils.provider_health import is_ollama_model_installed
        assert is_ollama_model_installed("") is False


# ---------------------------------------------------------------------------
# 3. is_api_provider_available
# ---------------------------------------------------------------------------

class TestIsApiProviderAvailable:
    def setup_method(self) -> None:
        # ENV-Variablen für diesen Test isolieren
        self._saved_env = {k: os.environ.get(k) for k in [
            "MISTRAL_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
            "GOOGLE_API_KEY", "XAI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY",
        ]}

    def teardown_method(self) -> None:
        for k, v in self._saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_known_provider_with_key(self) -> None:
        os.environ["MISTRAL_API_KEY"] = "sk-test"
        from utils.provider_health import is_api_provider_available
        assert is_api_provider_available("mistral") is True
        assert is_api_provider_available("Mistral") is True  # case-insensitive

    def test_known_provider_without_key(self) -> None:
        os.environ.pop("MISTRAL_API_KEY", None)
        from utils.provider_health import is_api_provider_available
        assert is_api_provider_available("mistral") is False

    def test_known_provider_empty_key(self) -> None:
        os.environ["MISTRAL_API_KEY"] = "   "
        from utils.provider_health import is_api_provider_available
        assert is_api_provider_available("mistral") is False

    def test_unknown_provider_returns_false(self) -> None:
        from utils.provider_health import is_api_provider_available
        assert is_api_provider_available("nonexistent") is False


# ---------------------------------------------------------------------------
# 4. validate_untested_card
# ---------------------------------------------------------------------------

class TestValidateUntestedCard:
    def test_valid_ollama_card_installed(self, ollama_installed_list: MagicMock) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", ollama_installed_list),
        ):
            from utils.provider_health import validate_untested_card
            card = {"model_id": "gemma3:12b", "provider": "ollama"}
            ok, reason = validate_untested_card(card)
        assert ok is True
        assert reason is None

    def test_ollama_card_not_installed(self, ollama_installed_list: MagicMock) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", ollama_installed_list),
        ):
            from utils.provider_health import validate_untested_card
            card = {"model_id": "qwen2.5vl:7b", "provider": "ollama"}
            ok, reason = validate_untested_card(card)
        assert ok is False
        assert reason and "ollama_model_not_installed" in reason

    def test_api_card_with_key(self, monkeypatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        from utils.provider_health import validate_untested_card
        card = {"model_id": "claude-opus-4-7", "provider": "anthropic"}
        ok, reason = validate_untested_card(card)
        assert ok is True

    def test_api_card_without_key(self, monkeypatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from utils.provider_health import validate_untested_card
        card = {"model_id": "claude-opus-4-7", "provider": "anthropic"}
        ok, reason = validate_untested_card(card)
        assert ok is False
        assert reason and "api_key_missing" in reason

    def test_llamacpp_no_path_is_ok(self) -> None:
        from utils.provider_health import validate_untested_card
        card = {"model_id": "hermes-4-14b", "provider": "llamacpp"}
        ok, _ = validate_untested_card(card)
        assert ok is True  # kein expliziter Pfad → wir vertrauen auf Benchmark

    def test_llamacpp_missing_path(self) -> None:
        from utils.provider_health import validate_untested_card
        card = {
            "model_id": "hermes-4-14b",
            "provider": "llamacpp",
            "llama_cpp_path": "/nonexistent/path/model.gguf",
        }
        ok, reason = validate_untested_card(card)
        assert ok is False
        assert reason and "llamacpp_path_missing" in reason

    def test_unknown_provider(self) -> None:
        from utils.provider_health import validate_untested_card
        card = {"model_id": "test", "provider": "madeup_provider"}
        ok, reason = validate_untested_card(card)
        assert ok is False
        assert reason and "unknown_provider" in reason

    def test_missing_model_id(self) -> None:
        from utils.provider_health import validate_untested_card
        ok, reason = validate_untested_card({"provider": "ollama"})
        assert ok is False
        assert reason == "missing_model_id"

    def test_missing_provider(self) -> None:
        from utils.provider_health import validate_untested_card
        ok, reason = validate_untested_card({"model_id": "x"})
        assert ok is False
        assert reason == "missing_provider"

    def test_invalid_card_type(self) -> None:
        from utils.provider_health import validate_untested_card
        ok, reason = validate_untested_card("not a dict")  # type: ignore[arg-type]
        assert ok is False
        assert reason == "card_invalid_type"


# ---------------------------------------------------------------------------
# 5. filter_testable_cards
# ---------------------------------------------------------------------------

class TestFilterTestableCards:
    def test_splits_testable_and_unreachable(self, ollama_installed_list: MagicMock) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", ollama_installed_list),
        ):
            from utils.provider_health import filter_testable_cards
            cards = [
                ("gemma3:12b", "Gemma 3 12B"),
                ("qwen2.5vl:7b", "Qwen 2.5 VL 7B"),
                ("nonexistent:7b", "Nonexistent 7B"),
            ]
            card_lookup = {
                "gemma3:12b": {"model_id": "gemma3:12b", "provider": "ollama"},
                "qwen2.5vl:7b": {"model_id": "qwen2.5vl:7b", "provider": "ollama"},
                "nonexistent:7b": {"model_id": "nonexistent:7b", "provider": "ollama"},
            }
            testable, unreachable = filter_testable_cards(cards, card_lookup)
        assert len(testable) == 1
        assert testable[0][0] == "gemma3:12b"
        assert len(unreachable) == 2
        unreachable_ids = {m[0] for m in unreachable}
        assert "qwen2.5vl:7b" in unreachable_ids
        assert "nonexistent:7b" in unreachable_ids

    def test_empty_input(self) -> None:
        from utils.provider_health import filter_testable_cards
        testable, unreachable = filter_testable_cards([])
        assert testable == []
        assert unreachable == []

    def test_unreachable_with_reason(self, ollama_installed_list: MagicMock) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/ollama"),
            patch("subprocess.run", ollama_installed_list),
        ):
            from utils.provider_health import filter_testable_cards
            cards = [("qwen2.5vl:7b", "Qwen VL")]
            card_lookup = {
                "qwen2.5vl:7b": {"model_id": "qwen2.5vl:7b", "provider": "ollama"},
            }
            _, unreachable = filter_testable_cards(cards, card_lookup)
        assert len(unreachable) == 1
        mid, name, reason = unreachable[0]
        assert mid == "qwen2.5vl:7b"
        assert "ollama_model_not_installed" in reason

    def test_warns_when_card_missing_in_filesystem_lookup(self, caplog) -> None:
        from utils.provider_health import filter_testable_cards

        cards = [("definitely_missing_model", "Missing Model")]
        with caplog.at_level("WARNING"):
            testable, unreachable = filter_testable_cards(cards, card_lookup=None)

        assert testable == []
        assert len(unreachable) == 1
        assert unreachable[0][0] == "definitely_missing_model"
        assert unreachable[0][2] == "unknown_provider:unknown"
        assert any("Pre-Flight-Card nicht gefunden" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# 6. _run_untested_tooluse_models — Pre-Flight + Unreachables-Report
# ---------------------------------------------------------------------------

class TestRunUntestedToolusePreflight:
    """End-to-end Test: prüft, dass nur testbare Modelle an Subprocess gehen
    und ein Unreachables-Report geschrieben wird."""

    def _make_fake_script(self, tmp_path: Path) -> Path:
        """Legt ein Skript-Dummy an, das _run_untested_tooluse_models
        als existenten Delegations-Target vorfindet."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        script_path = scripts_dir / "run_tooluse_benchmark.py"
        script_path.write_text("# dummy for tests\n", encoding="utf-8")
        return script_path

    def test_only_testable_models_delegated(self, tmp_path, monkeypatch) -> None:
        # ARRANGE: 2 untested Cards, eine testbar, eine nicht
        from scripts.core import benchmark_auto

        self._make_fake_script(tmp_path)

        # ENV sicherstellen
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

        # CARD_DIR und ROOT_DIR auf tmp umlenken
        monkeypatch.setattr(benchmark_auto, "CARD_DIR", tmp_path)
        monkeypatch.setattr(benchmark_auto, "ROOT_DIR", tmp_path)

        # 2 Cards anlegen — Filename entspricht der realen Konvention:
        # Doppelpunkte werden zu Unterstrichen (sonst ungültig auf manchen FS)
        (tmp_path / "gemma3_12b.json").write_text(json.dumps({
            "model_id": "gemma3:12b", "provider": "ollama", "display_name": "Gemma 3 12B"
        }))
        (tmp_path / "qwen2.5vl_7b.json").write_text(json.dumps({
            "model_id": "qwen2.5vl:7b", "provider": "ollama", "display_name": "Qwen 2.5 VL 7B"
        }))

        # Pre-Flight-Ergebnis deterministisch vorgeben — gemma3:12b testbar,
        # qwen2.5vl:7b nicht installiert.
        fake_filter = MagicMock(return_value=(
            [("gemma3:12b", "Gemma 3 12B")],
            [("qwen2.5vl:7b", "Qwen 2.5 VL 7B", "ollama_model_not_installed:qwen2.5vl:7b")],
        ))
        with patch.object(benchmark_auto, "filter_testable_cards", fake_filter):
            fake_sub = MagicMock(return_value=MagicMock(returncode=0))
            with patch("subprocess.run", fake_sub):
                models = [("gemma3:12b", "Gemma 3 12B"), ("qwen2.5vl:7b", "Qwen 2.5 VL 7B")]
                ok = benchmark_auto._run_untested_tooluse_models(
                    models, mcp_mode="mock", silent=True
                )

        # ACT-ASSERT: gemma3:12b ist testbar, qwen2.5vl:7b nicht
        assert ok is True
        # Subprocess wurde mit --models aufgerufen, NUR für gemma3:12b
        assert fake_sub.call_count == 1
        cmd = fake_sub.call_args[0][0]
        models_arg = cmd[cmd.index("--models") + 1]
        assert models_arg == "gemma3:12b"

        # Unreachables-Report wurde geschrieben
        report_files = list((tmp_path / "outputs").glob("tooluse_unreachable_*.json"))
        assert len(report_files) == 1
        report = json.loads(report_files[0].read_text())
        assert report["summary"]["unreachable"] == 1
        assert report["summary"]["testable"] == 1
        assert report["unreachable"][0]["model_id"] == "qwen2.5vl:7b"
        assert "ollama_model_not_installed" in report["unreachable"][0]["reason"]

    def test_all_unreachable_skips_subprocess(self, tmp_path, monkeypatch) -> None:
        from scripts.core import benchmark_auto

        self._make_fake_script(tmp_path)

        monkeypatch.setattr(benchmark_auto, "CARD_DIR", tmp_path)
        monkeypatch.setattr(benchmark_auto, "ROOT_DIR", tmp_path)

        (tmp_path / "qwen2_5vl_7b.json").write_text(json.dumps({
            "model_id": "qwen2.5vl:7b", "provider": "ollama"
        }))

        # Pre-Flight-Ergebnis deterministisch vorgeben — alle unerreichbar.
        fake_filter = MagicMock(return_value=(
            [],
            [("qwen2.5vl:7b", "Qwen VL", "ollama_model_not_installed:qwen2.5vl:7b")],
        ))
        with patch.object(benchmark_auto, "filter_testable_cards", fake_filter):
            fake_sub = MagicMock(return_value=MagicMock(returncode=0))
            with patch("subprocess.run", fake_sub):
                models = [("qwen2.5vl:7b", "Qwen VL")]
                ok = benchmark_auto._run_untested_tooluse_models(models, silent=True)

        # Kein Delegation, aber kein Fehler
        assert ok is True
        assert fake_sub.call_count == 0
        # Report geschrieben
        reports = list((tmp_path / "outputs").glob("tooluse_unreachable_*.json"))
        assert len(reports) == 1

    def test_empty_models_returns_false(self, monkeypatch) -> None:
        from scripts.core import benchmark_auto
        ok = benchmark_auto._run_untested_tooluse_models([])
        assert ok is False
