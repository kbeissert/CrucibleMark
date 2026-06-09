#!/usr/bin/env python3
"""Sanierung der 8 Modelle mit verwaisten Tooluse-Werten (Klasse-1-Anomalien).

Bereinigt in einem Rutsch:
  1. Card-Reset via update_model_card_tooluse_fields() für Modelle mit
     supports_tool_use != "untested"
  2. Tooluse-Audit-Files in outputs/audit_logs/<dir>/tooluse*.md entfernen
  3. Leaderboard-Zeilen aus tooluse_leaderboard.csv entfernen (mit Backup)

Modelle:
  mistral-large-2512, mistral-small-2603, deepseek/deepseek-v4-pro,
  nousresearch/hermes-4-405b, gpt-5_5, gemini-3.5-flash,
  gpt-oss:20b-cloud, nousresearch/hermes-4-70b
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from utils.model_utils import update_model_card_tooluse_fields  # noqa: E402

CARDS = [
    # (model_id, card_filename, audit_dir, in_leaderboard)
    ("mistral-large-2512", "mistral-large-2512.json", "mistral-large-2512", True),
    ("mistral-small-2603", "mistral-small-2603.json", "mistral-small-2603", True),
    ("deepseek/deepseek-v4-pro", "deepseek_deepseek-v4-pro.json", "deepseek_deepseek-v4-pro", True),
    ("nousresearch/hermes-4-405b", "nousresearch_hermes-4-405b.json", "nousresearch_hermes-4-405b", True),
    ("gpt-5_5", "gpt-5_5.json", "gpt-5_5", True),
    ("gemini-3.5-flash", "gemini-3_5-flash.json", "gemini-3_5-flash", True),
    ("gpt-oss:20b-cloud", "gpt-oss_20b-cloud.json", "gpt-oss_20b-cloud", False),
    ("nousresearch/hermes-4-70b", "nousresearch_hermes-4-70b.json", "nousresearch_hermes-4-70b", True),
]

CARDS_DIR = ROOT / "benchmark_scores" / "model_cards"
AUDIT_DIR = ROOT / "outputs" / "audit_logs"
LB_PATH = ROOT / "benchmark_scores" / "tooluse_leaderboard.csv"
LB_BAK = ROOT / "benchmark_scores" / "tooluse_leaderboard.csv.bak_pre8"


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
    lb_in_models = {m for m, _, _, in_lb in CARDS if in_lb}
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


if __name__ == "__main__":
    step1_reset_cards()
    step2_delete_audit_files()
    step3_delete_leaderboard_rows()
    print("\nSanierung abgeschlossen.")
