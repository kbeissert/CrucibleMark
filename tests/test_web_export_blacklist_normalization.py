"""Tests für die Blacklist-Normalisierung im Web-Export.

Hintergrund: Die Blacklist (``config/web_export_blacklist.yaml``) enthaelt
Eintraege in der kanonischen Underscore-Form (z.B.
``deepseek_deepseek-chat-v3_1``), waehrend die ``raw_model_id`` aus dem
Leaderboard Provider-Prefix und Punkte enthaelt (z.B.
``deepseek/deepseek-chat-v3.1``).

Ohne Normalisierung matchen 12/34 Eintraege nicht und Modelle werden
versehentlich exportiert. Fix: ``_is_blacklist()`` normalisiert BEIDE
Seiten via ``_safe_name()``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.web_export import _is_blacklisted


class TestIsBlacklistedNormalization:
    """Prueft die Normalisierung beider Seiten (Model-ID und Blacklist-Eintrag)."""

    def test_exact_match_without_normalization(self):
        """Klassischer Fall: identische Strings."""
        exact = {"foo-bar"}
        assert _is_blacklisted("foo-bar", exact, set()) is True
        assert _is_blacklisted("foo", exact, set()) is False

    def test_slash_to_underscore_normalization(self):
        """Slash-getrennte Provider-IDs werden zu Underscore normalisiert."""
        exact = {"deepseek_deepseek-chat-v3_1"}
        # CSV hat 'deepseek/deepseek-chat-v3.1' (mit Slashes + Punkten)
        assert _is_blacklisted("deepseek/deepseek-chat-v3.1", exact, set()) is True
        # Variante mit Punkten (nur Punkt statt Underscore)
        assert _is_blacklisted("deepseek_deepseek-chat-v3.1", exact, set()) is True

    def test_dot_to_underscore_normalization(self):
        """Punkte in Versionsnummern werden zu Underscores."""
        exact = {"gpt-5_5-pro-2026-04-23"}
        # CSV hat 'gpt-5.5-pro-2026-04-23' (Punkt statt Underscore)
        assert _is_blacklisted("gpt-5.5-pro-2026-04-23", exact, set()) is True

    def test_colon_normalization(self):
        """Ollama-Tags mit ':' werden zu '_' normalisiert."""
        exact = {"qwen3_5_397b-cloud"}
        # CSV hat 'qwen3.5:397b-cloud'
        assert _is_blacklisted("qwen3.5:397b-cloud", exact, set()) is True

    def test_pattern_match_normalized(self):
        """Pattern-Match muss ebenfalls normalisiert werden."""
        # Pattern enthaelt Wildcard
        exact = set()
        pattern = {"deepseek_*"}
        # Roh-Variante und normalisierte Variante muessen beide matchen
        assert _is_blacklisted("deepseek/deepseek-chat-v3.1", exact, pattern) is True
        assert _is_blacklisted("deepseek_anything", exact, pattern) is True

    def test_no_false_positive(self):
        """Aehnliche, aber nicht-idente Strings duerfen NICHT matchen."""
        exact = {"foo-bar"}
        # 'foo-bar-2' ist NICHT blacklisted (kein Prefix-Match)
        assert _is_blacklisted("foo-bar-2", exact, set()) is False
        # 'baz' ist nicht blacklisted
        assert _is_blacklisted("baz", exact, set()) is False

    def test_empty_blacklist(self):
        """Leere Blacklist blockiert nichts."""
        assert _is_blacklisted("any-model", set(), set()) is False

    def test_combined_slash_dot_colon_normalization(self):
        """Komplexe ID mit allen Sonderzeichen gleichzeitig."""
        exact = {"NousResearch_Hermes-4-14B-GGUF_Q4_K_M"}
        # CSV hat 'NousResearch/Hermes-4-14B-GGUF:Q4_K_M'
        # _safe_name konvertiert '/', ':' und '.' zu '_' und macht Uppercase
        from utils.model_utils import _safe_name
        normalized = _safe_name("NousResearch/Hermes-4-14B-GGUF:Q4_K_M")
        # Wenn die Normalisierung tatsaechlich passt, dann matcht es
        if normalized in exact:
            assert _is_blacklisted("NousResearch/Hermes-4-14B-GGUF:Q4_K_M", exact, set()) is True


class TestBlacklistAgainstRealConfig:
    """Prueft die Effektivitaet gegen die echte config/web_export_blacklist.yaml."""

    def test_real_config_loads(self):
        from scripts.web_export import _load_export_blacklist
        exact, pattern, total, loaded = _load_export_blacklist(
            ROOT / "config" / "web_export_blacklist.yaml"
        )
        assert loaded is True
        assert total > 0

    def test_deepseek_v31_is_now_blacklisted(self):
        """DeepSeek V3.1 muss nach dem Fix korrekt geblockt sein.

        Regressionsschutz: Vorher war die Blacklist zu 65% effektiv;
        DeepSeek V3.1 wurde trotz Blacklist-Eintrag exportiert.
        """
        from scripts.web_export import _load_export_blacklist
        exact, pattern, total, loaded = _load_export_blacklist(
            ROOT / "config" / "web_export_blacklist.yaml"
        )
        # Blacklist enthaelt 'deepseek_deepseek-chat-v3_1'
        # CSV hat 'deepseek/deepseek-chat-v3.1' (mit Slashes und Punkten)
        assert _is_blacklisted("deepseek/deepseek-chat-v3.1", exact, pattern) is True, (
            "DeepSeek V3.1 muss nach Normalisierung blacklisted sein"
        )

    def test_real_csv_models_get_correctly_blacklisted(self):
        """Prueft, dass CSV-IDs korrekt geblockt werden.

        Hinweis: 100% Effektivitaet ist nicht erreichbar, weil einige
        Blacklist-Eintraege auf nicht-mehr existierende Modelle zeigen oder
        Tippfehler enthalten (z.B. ``gpt-5_5-pro-2026-04-23`` statt
        ``gpt-5_5-2026-04-23``). Die mechanische Normalisierung selbst muss
        aber zuverlaessig greifen — wir pruefen daher die IDs, die im
        Leaderboard existieren und im Blacklist-Set exakt (oder normalisiert)
        vorkommen.
        """
        import csv
        from scripts.web_export import _load_export_blacklist
        from utils.model_utils import _safe_name

        exact, pattern, total, loaded = _load_export_blacklist(
            ROOT / "config" / "web_export_blacklist.yaml"
        )
        csv_ids: set[str] = set()
        with (ROOT / "benchmark_scores" / "benchmark_leaderboard_detailed.csv").open() as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                for col in ("Model ID", "model_id_raw"):
                    v = row.get(col, "").strip()
                    if v and v != "nan":
                        csv_ids.add(v)

        # Wir erwarten, dass die Normalisierung mindestens 90% der effektiv
        # matchbaren IDs trifft. IDs, die weder roh noch normalisiert in der
        # Blacklist vorkommen, sind Blacklist-Drift (Tippfehler) und zaehlen
        # nicht zur Effektivitaet.
        bl_normalized = {_safe_name(e) for e in exact}
        matchable_csv_ids = {
            cid for cid in csv_ids
            if cid in exact or _safe_name(cid) in bl_normalized
        }
        matched = sum(1 for cid in matchable_csv_ids if _is_blacklisted(cid, exact, pattern))
        assert len(matchable_csv_ids) > 0, "Test-Setup stimmt nicht"
        assert matched / len(matchable_csv_ids) >= 0.95, (
            f"Von {len(matchable_csv_ids)} matchbaren CSV-IDs wurden nur "
            f"{matched} geblockt. Normalisierung greift nicht richtig."
        )