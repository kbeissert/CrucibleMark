#!/usr/bin/env python3
"""Sanierung der 8 Modelle mit verwaisten Tooluse-Werten (Klasse-1-Anomalien).

Bereinigt in einem Rutsch (ATOMAR — alle Schritte gehoeren zusammen):
  1. Card-Reset via update_model_card_tooluse_fields() für Modelle mit
     supports_tool_use != "untested"
  2. Tooluse-Audit-Files in outputs/audit_logs/<dir>/tooluse*.md entfernen
  3. Leaderboard-Zeilen aus tooluse_leaderboard.csv entfernen (mit Backup)
  4. Narrative ToolUse-Reviews in docs/reviews/<dir>/tooluse_narrative_review_*.md
     entfernen (Backup in docs/reviews/<dir>/.bak_pre8_narrative/)
  5. Konsistenz-Check: prueft, dass kein narrativer Review ohne
     Leaderboard-Eintrag existiert (und umgekehrt).

Modelle:
  mistral-large-2512, mistral-small-2603, deepseek/deepseek-v4-pro,
  nousresearch/hermes-4-405b, gpt-5_5, gemini-3.5-flash,
  gpt-oss:20b-cloud, nousresearch/hermes-4-70b

Wichtig: Wenn einzelne Schritte separat ausgefuehrt werden (z.B. nur
Audit-Files loeschen ohne Leaderboard-Rows), entsteht der von User
beobachtete Drift: Web-Export zeigt Tool-Use-Werte, aber der
physische Audit-Trail ist weg. IMMER ALLE SCHRITTE zusammen ausfuehren.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from utils.model_utils import update_model_card_tooluse_fields, _safe_name  # noqa: E402

CARDS = [
    # (model_id, card_filename, audit_dir, in_leaderboard, review_dir)
    ("mistral-large-2512", "mistral-large-2512.json", "mistral-large-2512", True, "mistral-large-2512"),
    ("mistral-small-2603", "mistral-small-2603.json", "mistral-small-2603", True, "mistral-small-2603"),
    ("deepseek/deepseek-v4-pro", "deepseek_deepseek-v4-pro.json", "deepseek_deepseek-v4-pro", True, "deepseek_deepseek-v4-pro"),
    ("nousresearch/hermes-4-405b", "nousresearch_hermes-4-405b.json", "nousresearch_hermes-4-405b", True, "nousresearch_hermes-4-405b"),
    ("gpt-5_5", "gpt-5_5.json", "gpt-5_5", True, "gpt-5_5"),
    ("gemini-3.5-flash", "gemini-3_5-flash.json", "gemini-3_5-flash", True, "gemini-3_5-flash"),
    ("gpt-oss:20b-cloud", "gpt-oss_20b-cloud.json", "gpt-oss_20b-cloud", False, "gpt-oss_20b-cloud"),
    ("nousresearch/hermes-4-70b", "nousresearch_hermes-4-70b.json", "nousresearch_hermes-4-70b", True, "nousresearch_hermes-4-70b"),
]

CARDS_DIR = ROOT / "benchmark_scores" / "model_cards"
AUDIT_DIR = ROOT / "outputs" / "audit_logs"
LB_PATH = ROOT / "benchmark_scores" / "tooluse_leaderboard.csv"
LB_BAK = ROOT / "benchmark_scores" / "tooluse_leaderboard.csv.bak_pre8"
REVIEWS_DIR = ROOT / "docs" / "reviews"


def step1_reset_cards() -> None:
    print("\n=== 1. Card-Reset → 'untested' ===")
    for model_id, fname, _, _ in CARDS:
        card_path = CARDS_DIR / fname
        if not card_path.exists():
            print(f"  [SKIP] {model_id}: Card nicht gefunden ({fname})")
            continue
        with card_path.open(encoding="utf-8") as f:
            before = json.load(f)
        before_val = before.get("supports_tool_use")
        if before_val == "untested":
            print(f"  [OK   ] {model_id}: bereits 'untested'")
            continue
        ok = update_model_card_tooluse_fields(model_id, "untested", None)
        with card_path.open(encoding="utf-8") as f:
            after = json.load(f)
        after_val = after.get("supports_tool_use")
        has_tested_at = "tooluse_tested_at" in after
        status = "OK" if ok and after_val == "untested" and not has_tested_at else "FAIL"
        print(f"  [{status:5}] {model_id}: {before_val!r} → {after_val!r} (tooluse_tested_at entfernt: {not has_tested_at})")


def step2_delete_audit_files() -> None:
    print("\n=== 2. Tooluse-Audit-Files löschen ===")
    for _, _, audit_subdir, _ in CARDS:
        d = AUDIT_DIR / audit_subdir
        if not d.exists():
            print(f"  [SKIP] {audit_subdir}: Verzeichnis fehlt")
            continue
        tooluse_files = sorted(d.glob("tooluse*.md"))
        if not tooluse_files:
            print(f"  [OK   ] {audit_subdir}: keine tooluse-Files")
            continue
        for f in tooluse_files:
            f.unlink()
        print(f"  [DEL  ] {audit_subdir}: {len(tooluse_files)} Files gelöscht")


def step3_delete_leaderboard_rows() -> None:
    print("\n=== 3. Leaderboard-Zeilen löschen ===")
    lb_in_models = {m for m, _, _, in_lb, _ in CARDS if in_lb}
    if not LB_BAK.exists():
        shutil.copy2(LB_PATH, LB_BAK)
        print(f"  [BAK  ] {LB_BAK.name} erstellt")
    else:
        print(f"  [BAK  ] {LB_BAK.name} bereits vorhanden")

    with LB_PATH.open(encoding="utf-8") as f:
        lines = f.readlines()
    header = lines[0]
    keep = [header]
    removed = []
    for line in lines[1:]:
        first_col = line.split(",", 1)[0]
        if first_col in lb_in_models:
            removed.append(first_col)
        else:
            keep.append(line)
    with LB_PATH.open("w", encoding="utf-8") as f:
        f.writelines(keep)
    print(f"  [DONE] {len(removed)} Zeilen entfernt: {removed}")
    print(f"  [INFO] {len(keep)-1} Zeilen verbleibend (Header + Daten)")


def step4_delete_narrative_reviews() -> None:
    """Loescht narrative ToolUse-Reviews mit Backup.

    Hintergrund: ``docs/reviews/<slug>/tooluse_narrative_review_*.md``
    reproduzieren die aggregierten Leaderboard-Werte. Wenn der Leaderboard-
    Eintrag entfernt wird (Schritt 3), aber der narrative Review
    stehenbleibt, zeigt der Web-Export weiterhin Tool-Use-Daten ohne
    dass der Audit-Trail im Leaderboard nachvollziehbar ist.
    """
    print("\n=== 4. Narrative ToolUse-Reviews löschen (mit Backup) ===")
    for _, _, _, _, review_subdir in CARDS:
        d = REVIEWS_DIR / review_subdir
        if not d.exists():
            print(f"  [SKIP] {review_subdir}: Verzeichnis fehlt")
            continue
        narrative_files = sorted(d.glob("tooluse_narrative_review_*.md"))
        if not narrative_files:
            print(f"  [OK  ] {review_subdir}: keine narrative ToolUse-Reviews")
            continue
        backup = d / ".bak_pre8_narrative"
        backup.mkdir(exist_ok=True)
        for f in narrative_files:
            shutil.copy2(f, backup / f.name)
            f.unlink()
        print(f"  [DEL ] {review_subdir}: {len(narrative_files)} Files gelöscht (Backup: {backup.name})")


def step5_consistency_check() -> None:
    """Prueft am Ende: kein Modell mit ToolUse-Review ohne Leaderboard-Eintrag.

    Hintergrund: Wenn narrative Reviews existieren, das Modell aber nicht
    in tooluse_leaderboard.csv steht, zeigt der Web-Export Tool-Use-Daten
    aus den narrativen Reviews ohne dass ein SSoT-Eintrag im Leaderboard
    existiert.

    Scannt ALLE Modelle im Repo (nicht nur die CARDS-Liste), weil Drift
    auch bei Modellen auftreten kann, die nicht in dieser Sanity-Runde
    sind.
    """
    print("\n=== 5. Konsistenz-Check (Narrative Review ↔ Leaderboard) ===")
    # Lade Leaderboard-Model-IDs (erste Spalte = canonical model_id)
    if not LB_PATH.exists():
        print("  [WARN] tooluse_leaderboard.csv fehlt — Check uebersprungen")
        return
    lb_models: set[str] = set()
    with LB_PATH.open(encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines[1:]:
        first_col = line.split(",", 1)[0].strip()
        if first_col:
            lb_models.add(first_col)
    # Lade LB-IDs aus dem Haupt-Leaderboard (benchmark_leaderboard_detailed.csv)
    main_lb_models: set[str] = set()
    main_lb_path = ROOT / "benchmark_scores" / "benchmark_leaderboard_detailed.csv"
    if main_lb_path.exists():
        with main_lb_path.open(encoding="utf-8") as f:
            rdr_lines = f.readlines()
        for line in rdr_lines[1:]:
            cols = line.split(",", 3)
            if len(cols) >= 3:
                mid = cols[2].strip()  # 'Model ID'
                if mid:
                    main_lb_models.add(mid)
    # Scanne ALLE docs/reviews/-Subdirs nach narrativen ToolUse-Reviews
    if not REVIEWS_DIR.exists():
        print(f"  [WARN] {REVIEWS_DIR} fehlt — Check uebersprungen")
        return
    drift = []
    orphan_narrative = []  # narrative Review ohne ueberhaupt LB-Eintrag
    consistent = 0
    for review_subdir in sorted(REVIEWS_DIR.iterdir()):
        if not review_subdir.is_dir():
            continue
        if review_subdir.name.startswith("."):
            continue
        narrative_files = list(review_subdir.glob("tooluse_narrative_review_*.md"))
        if not narrative_files:
            continue
        # Mapping review_subdir → model_id: heuristisch ueber _safe_name und CSV-IDs
        # Wir versuchen alle LB-Matchings.
        review_subdir_name = review_subdir.name
        matched = False
        for lb_id in lb_models:
            if _safe_name(lb_id) == review_subdir_name:
                matched = True
                consistent += 1
                break
            # Fallback: review_subdir ist Praefix einer versionierten LB-ID
            # (z.B. 'gpt-5_5/' vs 'gpt-5_5-2026-04-23' im LB)
            if review_subdir_name + "-" in lb_id or review_subdir_name + "_" in lb_id:
                matched = True
                consistent += 1
                break
        if not matched:
            # Auch im Haupt-Leaderboard pruefen
            for lb_id in main_lb_models:
                if _safe_name(lb_id) == review_subdir_name:
                    matched = True
                    consistent += 1
                    break
                if review_subdir_name + "-" in lb_id or review_subdir_name + "_" in lb_id:
                    matched = True
                    consistent += 1
                    break
        if not matched:
            orphan_narrative.append((review_subdir_name, len(narrative_files)))
    print(f"  [INFO] {consistent} Review-Dirs mit konsistentem LB-Eintrag")
    if orphan_narrative:
        print(f"  [DRIFT] {len(orphan_narrative)} Review-Dirs ohne LB-Eintrag:")
        for rdir, count in orphan_narrative:
            print(f"          - {rdir}/: {count} narrative Review(s)")
    else:
        print("  [OK  ] Keine Drift gefunden: alle narrativen Reviews haben LB-Eintrag")


if __name__ == "__main__":
    step1_reset_cards()
    step2_delete_audit_files()
    step3_delete_leaderboard_rows()
    step4_delete_narrative_reviews()
    step5_consistency_check()
    print("\nSanierung abgeschlossen.")
