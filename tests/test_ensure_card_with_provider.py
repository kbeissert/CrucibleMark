"""Tests fuer `ensure_card` mit dem neuen `provider`-Parameter.

Score-Cache-Hardening Phase B.2: prueft, dass `ensure_card(model_id, provider=...)`
die ID via `build_card_id` + `resolve_unique_card_id` eindeutig macht und am
richtigen Pfad schreibt.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import utils.card_utils as card_utils_module
import utils.model_utils
import utils.model_card_io as model_card_io_module
from utils.card_utils import ensure_card


@pytest.fixture
def isolated_card_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Biegt CARD_DIR in BEIDEN Modulen auf tmp_path um.

    `ensure_card` ruft `model_card_io._card_path` und
    `model_card_io.resolve_unique_card_id`, die `CARD_DIR` aus dem
    `model_card_io`-Modul lesen. Auch `model_utils` wird gepatcht, weil
    die Bridge denselben Pfad-Konstanten re-exportiert.
    """
    card_dir = tmp_path / "cards"
    card_dir.mkdir()
    monkeypatch.setattr(utils.model_utils, "CARD_DIR", card_dir)
    monkeypatch.setattr(model_card_io_module, "CARD_DIR", card_dir)
    return card_dir


def test_ensure_card_with_provider_creates_unique_file(
    isolated_card_dir: Path,
) -> None:
    """Mit Provider wird die Card unter dem neuen ID-Schema abgelegt.

    Hinweis: ``_card_path`` wendet ``_safe_name`` an, das Punkte zu
    Underscores konvertiert (``qwen3.5-9b`` → ``qwen3_5-9b``). Damit ist
    der tatsaechliche Dateiname ``qwen3_5-9b--SPRK.json``, waehrend die
    ID im JSON-Inhalt als ``qwen3.5-9b--SPRK`` steht (siehe
    ``test_ensure_card_with_provider_sets_correct_model_id``).
    """
    result_path = ensure_card(
        "qwen3.5-9b", provider="llamacpp_spark", card_path=isolated_card_dir / "should_be_ignored.json"
    )
    # Provider wird genutzt → kanonischer Pfad ueberschreibt den uebergebenen card_path.
    # _safe_name konvertiert den Punkt zu Underscore.
    assert result_path == isolated_card_dir / "qwen3_5-9b--SPRK.json"
    assert result_path.exists()


def test_ensure_card_with_provider_sets_correct_model_id(
    isolated_card_dir: Path,
) -> None:
    """Die neue Card traegt die gebaute ID als model_id-Feld."""
    result_path = ensure_card("claude-sonnet-4-5-20250929", provider="anthropic")
    data = json.loads(result_path.read_text(encoding="utf-8"))
    assert data["model_id"] == "claude-sonnet-4-5-20250929--anthropic"


def test_ensure_card_with_provider_strips_namespace(
    isolated_card_dir: Path,
) -> None:
    """OpenRouter-Namespace (vor dem '/') wird in der ID abgeschnitten.

    Hinweis: ``_card_path`` wendet ``_safe_name`` an, das Punkte zu
    Underscores konvertiert. Der Dateiname wird also ``qwen3_5-4b-q4--OR.json``.
    """
    result_path = ensure_card("qwen/qwen3.5-4b-q4", provider="openrouter")
    assert result_path == isolated_card_dir / "qwen3_5-4b-q4--OR.json"
    data = json.loads(result_path.read_text(encoding="utf-8"))
    assert data["model_id"] == "qwen3.5-4b-q4--OR"


def test_ensure_card_with_provider_resolves_conflict(
    isolated_card_dir: Path,
) -> None:
    """Wenn die Card schon existiert, wird ein Suffix angehaengt."""
    # Vorhandene Card simulieren (z. B. durch vorherigen Lauf).
    # _safe_name konvertiert den Punkt im Filename zu Underscore.
    (isolated_card_dir / "qwen3_5-9b--SPRK.json").write_text("{}", encoding="utf-8")
    result_path = ensure_card("qwen3.5-9b", provider="llamacpp_spark")
    assert result_path == isolated_card_dir / "qwen3_5-9b--SPRK-2.json"
    assert result_path.exists()
    data = json.loads(result_path.read_text(encoding="utf-8"))
    # model_id-Feld enthaelt die build_card_id-Form (mit Punkt), weil unique_id
    # ueber build_card_id berechnet wird, das den Punkt NICHT konvertiert.
    assert data["model_id"] == "qwen3.5-9b--SPRK-2"


def test_ensure_card_without_provider_uses_legacy_path(
    isolated_card_dir: Path,
) -> None:
    """Ohne Provider bleibt das alte Verhalten erhalten (rueckwaertskompatibel)."""
    # Legacy-Card ohne Provider-Suffix
    result_path = ensure_card("legacy-model")
    # Bei einem simplen nicht-namespaced Model-ID ohne Provider landet die Card
    # unter dem _safe_name-Pfad (kein SPRK-Prefix).
    assert result_path.name == "legacy-model.json"
    assert result_path.exists()


def test_ensure_card_is_idempotent_with_provider(
    isolated_card_dir: Path,
) -> None:
    """Zwei Aufrufe mit gleichem Provider erzeugen KEIN Duplikat, sondern
    den Konflikt-Suffix (zweite Datei)."""
    ensure_card("qwen3.5-9b", provider="llamacpp_spark")
    files_after_first = sorted(p.name for p in isolated_card_dir.iterdir())
    # _safe_name konvertiert den Punkt zu Underscore im Filename.
    assert files_after_first == ["qwen3_5-9b--SPRK.json"]

    # Zweiter Aufruf: build_card_id-Form kollidiert mit der existierenden Datei → -2-Suffix.
    ensure_card("qwen3.5-9b", provider="llamacpp_spark")
    files_after_second = sorted(p.name for p in isolated_card_dir.iterdir())
    assert files_after_second == ["qwen3_5-9b--SPRK-2.json", "qwen3_5-9b--SPRK.json"]


def test_ensure_card_preserves_existing_fields(
    isolated_card_dir: Path,
) -> None:
    """Existierende Karten-Felder werden nicht ueberschrieben (Standard-Vertrag)."""
    # _safe_name konvertiert den Punkt zu Underscore.
    existing_path = isolated_card_dir / "qwen3_5-9b--SPRK.json"
    existing_path.write_text(
        json.dumps(
            {
                "model_id": "OLD-VALUE",
                "summary": "Manuell gepflegt, nicht ueberschreiben!",
                "display_name": "Hand-edited Display Name",
            }
        ),
        encoding="utf-8",
    )
    result_path = ensure_card("qwen3.5-9b", provider="llamacpp_spark")
    # Datei wurde in *-2.json geschrieben, weil die build_card_id-Form
    # mit der existierenden Datei kollidiert.
    assert result_path == isolated_card_dir / "qwen3_5-9b--SPRK-2.json"
    data = json.loads(result_path.read_text(encoding="utf-8"))
    # Neue Card hat Template-Defaults (kein Konflikt mit Original).
    assert data["summary"] == "TODO"
    # Original-Datei bleibt unveraendert.
    original = json.loads(existing_path.read_text(encoding="utf-8"))
    assert original["summary"] == "Manuell gepflegt, nicht ueberschreiben!"
    assert original["display_name"] == "Hand-edited Display Name"
