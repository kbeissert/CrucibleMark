"""
card_sync.py — SSoT-Sync zwischen Card-Template und Karten-Dateien
===================================================================

Synchronisiert JSON-Karten in ``benchmark_scores/{provider,model}_cards/`` mit
dem kanonischen Python-Dict-Template (``_PROVIDER_CARD_TEMPLATE`` aus
``utils.vendor_card_template``, ``_CARD_TEMPLATE`` aus ``utils.card_utils``).

Zwei Sync-Richtungen:

1. **Add (Vorwärts):** Felder, die im Template neu sind, fehlen aber in der
   Karte → mit Default-Wert ergänzen. **Automatisch**, kein Prompt.

2. **Delete (Rückwärts):** Felder, die in der Karte sind, aber nicht mehr im
   Template → aus Karte entfernen. **Mit Bestätigungs-Prompt** (kann mit
   ``--yes`` übersprungen werden), weil Datenverlust irreversibel ist.

3. **Beibehalten:** Felder, die in Karte und Template sind → unverändert.

Nicht-Template-Felder (z.B. ``tooluse_*``-Legacy-Felder in Model Cards) werden
**nicht angetastet** — sie sind Drift, aber nicht Teil des Sync-Auftrags.

Idempotent: Mehrfacher Aufruf ohne Template-Änderung ist ein No-Op.

Verwendung als Library:
    >>> from utils.card_sync import sync_card, plan_sync
    >>> plan = plan_sync(card_path, "vendor")
    >>> for action in plan.actions:
    ...     print(action)
    >>> sync_card(card_path, "provider", yes=True)

CLI:
    python scripts/analysis/sync_cards.py --card-type provider --dry-run
    python scripts/analysis/sync_cards.py --card-type model --yes
    python scripts/analysis/sync_cards.py --card-type all
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pfade
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).parent.parent
PROVIDER_CARDS_DIR = ROOT_DIR / "benchmark_scores" / "vendor_cards"
MODEL_CARDS_DIR = ROOT_DIR / "benchmark_scores" / "model_cards"

CardType = Literal["model", "vendor"]


# ---------------------------------------------------------------------------
# Datenmodelle
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SyncAction:
    """Eine einzelne Sync-Operation auf einer Karte."""

    kind: Literal["add", "delete", "keep"]
    field: str
    reason: str = ""

    def __str__(self) -> str:  # noqa: D401 - dunder für CLI
        prefix = {"add": "+", "delete": "-", "keep": " "}[self.kind]
        suffix = f"  ({self.reason})" if self.reason else ""
        return f"  {prefix} {self.field}{suffix}"


@dataclass
class SyncPlan:
    """Sync-Plan für eine einzelne Karte."""

    card_path: Path
    card_type: CardType
    actions: list[SyncAction] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(a.kind in ("add", "delete") for a in self.actions)

    @property
    def add_count(self) -> int:
        return sum(1 for a in self.actions if a.kind == "add")

    @property
    def delete_count(self) -> int:
        return sum(1 for a in self.actions if a.kind == "delete")

    @property
    def keep_count(self) -> int:
        return sum(1 for a in self.actions if a.kind == "keep")

    def format_report(self) -> str:
        """Formatierter Report für CLI-Output."""
        lines = [f"--- {self.card_path.name} ({self.card_type}) ---"]
        if not self.has_changes:
            lines.append("  (no changes)")
        else:
            for action in self.actions:
                if action.kind != "keep":
                    lines.append(str(action))
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Template-Lookup
# ---------------------------------------------------------------------------


def get_template_field_names(card_type: CardType) -> set[str]:
    """Gibt die kanonischen Feldnamen aus dem Python-Dict-Template zurück."""
    if card_type == "vendor":
        from utils.vendor_card_template import _PROVIDER_CARD_TEMPLATE  # noqa: PLC0415
        return set(_PROVIDER_CARD_TEMPLATE.keys())
    if card_type == "model":
        from utils.card_utils import _CARD_TEMPLATE  # noqa: PLC0415
        return set(_CARD_TEMPLATE.keys())
    raise ValueError(f"Unbekannter card_type: {card_type!r}")


def get_template_default(card_type: CardType, field_name: str) -> Any:
    """Gibt den Default-Wert für ein Feld aus dem Template zurück."""
    if card_type == "vendor":
        from utils.vendor_card_template import _PROVIDER_CARD_TEMPLATE  # noqa: PLC0415
        return _PROVIDER_CARD_TEMPLATE.get(field_name)
    if card_type == "model":
        from utils.card_utils import _CARD_TEMPLATE  # noqa: PLC0415
        return _CARD_TEMPLATE.get(field_name)
    raise ValueError(f"Unbekannter card_type: {card_type!r}")


# ---------------------------------------------------------------------------
# Planung
# ---------------------------------------------------------------------------


def plan_sync(card_path: Path, card_type: CardType) -> SyncPlan:
    """Berechnet den Sync-Plan für eine Karte, ohne sie zu verändern.

    Regeln:
    - Felder, die in Karte UND Template sind → ``keep``
    - Felder, die im Template neu sind, aber in Karte fehlen → ``add``
    - Felder, die in Karte sind, aber NICHT im Template → ``delete``
      (außer ``_index`` / ``_backup``-Sentinels und ``tooluse_*``-Legacy)
    - ``provider_id`` / ``model_id`` werden nie gelöscht (Pflicht)
    """
    template_fields = get_template_field_names(card_type)
    sentinel_files = {"_index.json"}
    if card_path.name in sentinel_files:
        return SyncPlan(card_path=card_path, card_type=card_type)

    try:
        card_data = json.loads(card_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Kann %s nicht lesen: %s", card_path, e)
        return SyncPlan(card_path=card_path, card_type=card_type)

    if not isinstance(card_data, dict):
        return SyncPlan(card_path=card_path, card_type=card_type)

    card_fields = set(card_data.keys())
    actions: list[SyncAction] = []

    # Pflicht-IDs werden nie gelöscht
    protected_ids = {"vendor_id"} if card_type == "vendor" else {"model_id"}

    # tooluse_*-Legacy in Model Cards: toleriert vom Validator, nicht löschen
    legacy_prefixes: tuple[str, ...] = ("tooluse_",) if card_type == "model" else ()

    # 1) Add: Template-Felder, die in der Karte fehlen
    for field_name in sorted(template_fields):
        if field_name in card_fields:
            actions.append(SyncAction("keep", field_name))
        else:
            actions.append(
                SyncAction("add", field_name, reason="fehlt in Karte, im Template vorhanden")
            )

    # 2) Delete: Karten-Felder, die nicht im Template sind
    for field_name in sorted(card_fields):
        if field_name in template_fields:
            continue
        if field_name in protected_ids:
            actions.append(
                SyncAction("keep", field_name, reason="Pflicht-ID, nicht löschbar")
            )
            continue
        if any(field_name.startswith(prefix) for prefix in legacy_prefixes):
            actions.append(
                SyncAction("keep", field_name, reason="Legacy-Feld (vom Validator toleriert)")
            )
            continue
        actions.append(
            SyncAction(
                "delete",
                field_name,
                reason="nicht mehr im Template definiert",
            )
        )

    return SyncPlan(card_path=card_path, card_type=card_type, actions=actions)


# ---------------------------------------------------------------------------
# Ausführung
# ---------------------------------------------------------------------------


def apply_sync(
    card_path: Path,
    card_type: CardType,
    *,
    dry_run: bool = False,
    yes: bool = False,
    confirm_fn=None,
) -> SyncPlan:
    """Plant und führt den Sync für eine Karte aus.

    Args:
        card_path: Pfad zur Card-Datei.
        card_type: ``"model"`` oder ``"provider"``.
        dry_run: Wenn True, wird nichts geschrieben — nur Report.
        yes: Wenn True, werden Löschungen ohne Rückfrage durchgeführt.
        confirm_fn: Optional Callable(bool) -> bool für Tests. Wenn None,
            wird im Default-Modus ``input()`` verwendet.

    Returns:
        ``SyncPlan`` mit allen geplanten Aktionen.
    """
    plan = plan_sync(card_path, card_type)

    if not plan.has_changes:
        return plan

    if not dry_run:
        # Lösch-Bestätigung (gesammelt für die Karte)
        deletes = [a for a in plan.actions if a.kind == "delete"]
        if deletes and not yes:
            field_list = ", ".join(a.field for a in deletes)
            prompt = (
                f"\n{plan.card_path.name}: {len(deletes)} Feld(er) entfernen "
                f"[{field_list}]? (j/N) "
            )
            if confirm_fn is not None:
                confirmed = confirm_fn(prompt)
            else:
                try:
                    confirmed = input(prompt).strip().lower() in ("j", "y", "ja", "yes")
                except (EOFError, KeyboardInterrupt):
                    confirmed = False
            if not confirmed:
                logger.info(
                    "Übersprungen (%s): keine Bestätigung für Löschung.",
                    plan.card_path.name,
                )
                # Atomarer Sync: Karte unverändert lassen. Leerer Plan
                # signalisiert dem Aufrufer "nichts passiert".
                return SyncPlan(
                    card_path=plan.card_path,
                    card_type=plan.card_type,
                    actions=[],
                )

        # Karte neu schreiben
        try:
            card_data = json.loads(card_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Kann %s nicht lesen beim Apply: %s", card_path, e)
            return plan

        new_data: dict[str, Any] = {}
        for action in plan.actions:
            if action.kind == "delete":
                continue
            if action.field in card_data:
                new_data[action.field] = card_data[action.field]
            elif action.kind == "add":
                default = get_template_default(card_type, action.field)
                # Mutable Defaults deep-kopieren
                from copy import deepcopy  # noqa: PLC0415
                new_data[action.field] = deepcopy(default)

        card_path.write_text(
            json.dumps(new_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        logger.info("Aktualisiert: %s", plan.card_path.name)

    return plan


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------


def collect_card_paths(card_type: CardType) -> list[Path]:
    """Sammelt alle Karten-Pfade eines Typs (ohne _index.json)."""
    cards_dir = PROVIDER_CARDS_DIR if card_type == "vendor" else MODEL_CARDS_DIR
    if not cards_dir.exists():
        return []
    return sorted(
        p for p in cards_dir.glob("*.json") if p.name not in {"_index.json"}
    )


def sync_all(
    card_type: CardType,
    *,
    dry_run: bool = False,
    yes: bool = False,
    confirm_fn=None,
) -> list[SyncPlan]:
    """Synchronisiert alle Karten eines Typs.

    Args:
        card_type: ``"model"`` oder ``"provider"``.
        dry_run: Vorschau-Modus.
        yes: Skip der Lösch-Bestätigung.
        confirm_fn: Test-Hook für ``input()``.

    Returns:
        Liste aller ``SyncPlan``-Objekte.
    """
    plans: list[SyncPlan] = []
    for path in collect_card_paths(card_type):
        plan = apply_sync(
            path, card_type, dry_run=dry_run, yes=yes, confirm_fn=confirm_fn
        )
        plans.append(plan)
    return plans


def format_summary(plans: list[SyncPlan]) -> str:
    """Formatiert eine Zusammenfassung über alle Pläne für CLI-Output."""
    changed = [p for p in plans if p.has_changes]
    lines = [
        "=== Card-Sync Zusammenfassung ===",
        f"  Cards verarbeitet:   {len(plans)}",
        f"  Cards mit Änderungen: {len(changed)}",
        f"  Adds:    {sum(p.add_count for p in plans)}",
        f"  Deletes: {sum(p.delete_count for p in plans)}",
        "",
    ]
    for plan in plans:
        if plan.has_changes:
            lines.append(plan.format_report())
            lines.append("")
    if not changed:
        lines.append("Alle Karten sind synchron mit dem Template.")
    return "\n".join(lines)
