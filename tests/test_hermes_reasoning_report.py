"""
Tests für scripts/analysis/hermes_reasoning_report.py — Hermes-Reasoning-Report.

Deckt ab:
    - read_sessions/_apply_usage_batch (Haupt-Loop vs. Auxiliary-task, Reasoning-Text)
    - _suffix_matches             (Audit-Writer demmt Markdown-Headings)
    - match_session               (Priorität text → ende → tokens, Zeit-Tiebreak,
                                   Markierung bei unklarer Zeit/Gleichstand)
    - module_of / _aggregate      (Modulzuordnung, Mittelwerte)
    - build_report                (End-to-End gegen Temp-DB + Temp-Audit-Logs)

Keine echte State-DB, keine Netzwerkzugriffe.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from scripts.analysis import hermes_reasoning_report as hr

TS = datetime(2026, 9, 16, 16, 36, 24).timestamp()


@pytest.fixture
def db(tmp_path) -> Path:
    """Zwei Sessions: eine mit Heading-demmt Antwort, eine ohne Reasoning."""
    path = tmp_path / "state.db"
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE sessions (id TEXT PRIMARY KEY, started_at REAL, model TEXT);
        CREATE TABLE session_model_usage (
            session_id TEXT, task TEXT, api_call_count INTEGER, input_tokens INTEGER,
            output_tokens INTEGER, cache_read_tokens INTEGER, reasoning_tokens INTEGER,
            model TEXT DEFAULT 'M');
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT,
            content TEXT, reasoning_content TEXT);
    """)
    con.executemany(
        "INSERT INTO sessions VALUES (?,?,?)",
        [("s1", TS, "Qwen3.8-27B-NVFP4"), ("s2", TS + 60, "Qwen3.8-27B-NVFP4")],
    )
    con.executemany(
        "INSERT INTO session_model_usage (session_id,task,api_call_count,input_tokens,"
        "output_tokens,cache_read_tokens,reasoning_tokens) VALUES (?,?,?,?,?,?,?)",
        [("s1", "", 2, 12371, 900, 9600, 300), ("s1", "title_generation", 1, 254, 13, 0, 0),
         ("s2", "", 1, 12371, 400, 0, 0)],
    )
    con.executemany(
        "INSERT INTO messages (session_id,role,content,reasoning_content) VALUES (?,?,?,?)",
        [("s1", "user", "Prompt A", None),
         ("s1", "assistant", "Ich prüfe kurz.", "Denktext kurz"),
         ("s1", "assistant", "# Ergebnis\n\n" + "x" * 300, "y" * 500),
         ("s2", "user", "Prompt B", None),
         ("s2", "assistant", "Nur Antwort " * 10, None)],
    )
    con.commit()
    con.close()
    return path


@pytest.fixture
def audit(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "audit_logs" / "m"
    root.mkdir(parents=True)
    (root / "a1.md").write_text(
        "# Audit\n## 1. Prompt\n\n> User: Prompt A\n\n## 2. Model Response / Antwort\n\n"
        "Ich prüfe kurz.\n\n### Ergebnis\n\n" + "x" * 300 + "\n\n## 3. Evaluation\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(hr, "AUDIT_ROOT", tmp_path / "audit_logs")
    return tmp_path / "audit_logs"


class TestReadSessions:
    def test_trennt_hauptloop_und_auxiliary(self, db):
        s1 = next(s for s in hr.read_sessions(db, "") if s.session_id == "s1")
        assert s1.api_calls == 2 and s1.output_tokens == 900
        assert s1.reasoning_tokens == 300 and s1.cache_read_tokens == 9600
        assert s1.aux_calls == 1 and s1.aux_tokens == 13

    def test_sammelt_reasoning_text_und_finale_nachricht(self, db):
        s1 = next(s for s in hr.read_sessions(db, "") if s.session_id == "s1")
        assert s1.reasoning_msgs == 2 and s1.reasoning_chars == 500 + len("Denktext kurz")
        assert s1.final_content.startswith("# Ergebnis")

    def test_filtert_nach_modell(self, db):
        assert hr.read_sessions(db, "anderes-modell") == []


class TestJoin:
    def test_suffix_trotz_heading_daemmung(self, db, audit):
        sessions = hr.read_sessions(db, "")
        row = {"asset_id": "a1", "output_tokens": 900, "ts": TS}
        sess, method = hr.match_session(row, sessions, "m")
        assert method in ("antwort-text", "antwort-ende")
        assert sess is not None and sess.session_id == "s1"

    def test_token_rueckfall_ohne_audit_log(self, db, audit):
        row = {"asset_id": "unbekannt", "output_tokens": 400, "ts": TS + 30}
        sess, method = hr.match_session(row, hr.read_sessions(db, ""), "m")
        assert method == "output-tokens" and sess.session_id == "s2"

    def test_kein_treffer(self, db, audit):
        sess, method = hr.match_session(
            {"asset_id": "x", "output_tokens": 999999, "ts": TS}, hr.read_sessions(db, ""), "m")
        assert sess is None and method == "—"

    def test_kuerzer_als_min_suffix_matchet_nicht(self):
        assert hr._suffix_matches("kurz", "text kurz ende") is False

    def test_unbekannte_zeit_wird_markiert_statt_still_gewaehlt(self, db, audit):
        row = {"asset_id": "unbekannt", "output_tokens": 400, "ts": None}
        sess, method = hr.match_session(row, hr.read_sessions(db, ""), "m")
        assert sess is not None and method == "output-tokens:zeit-unbekannt"

    def test_gleichstand_wird_markiert(self, db, audit):
        sessions = hr.read_sessions(db, "")
        pick, note = hr._nearest(sessions, (TS + TS + 60) / 2)
        assert note == "mehrdeutig" and pick.session_id == "s1"

    def test_to_epoch_liefert_none_bei_unparsebar(self):
        assert hr._to_epoch("kein-timestamp") is None
        assert hr._to_epoch("2026-09-16 16:36:24") == TS


class TestAggregation:
    @pytest.mark.parametrize(
        "asset,expected",
        [("code_quality_001", "code_quality"), ("cli005", "cli"),
         ("reasoning_metacog_002", "metacog (Tier 3)"), ("reasoning_5b_001", "reasoning T0-T2"),
         ("ux_writing_001", "ux")],
    )
    def test_modulzuordnung(self, asset, expected):
        assert hr.module_of(asset) == expected

    def test_build_report_ohne_session_treffer(self, db, audit, monkeypatch):
        monkeypatch.setattr(hr, "read_sessions", lambda *a, **k: [])
        rows = [{"asset_id": "a1", "score": 80.0, "output_tokens": 900, "input_tokens": 1,
                 "response_length": 1, "execution_time": 1.0, "ts": TS}]
        rep = hr.build_report(rows, [], "m")
        assert rep["tasks"][0]["reasoning_tokens"] is None
        assert rep["modules"]["a1"]["matched"] == 0  # module_of("a1") → Präfix selbst
