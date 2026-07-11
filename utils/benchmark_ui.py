"""
Benchmark Terminal UI Component.
================================

Handles all terminal output for benchmark modules, following strict separation of concerns.
This allows the test logic to remain clean and the UI to be easily swappable or updated.

Design Principles:
- Single Source of Truth for Output Formatting
- Support for detailed progress tracking (Blocks, Tokens, Costs)
- Clean visual separation (Headers, Boxes, Summaries)
"""

import time
import logging
import unicodedata
from typing import TypeVar
from collections.abc import Callable

logger = logging.getLogger(__name__)

# Constants
VARIATION_SELECTOR_16 = 0xFE0F
SUPPLEMENTARY_PLANE_START = 0x1F000
TOKEN_K_THRESHOLD = 999
PC_THRESHOLD_STRONG_NEG = -2.0
PC_THRESHOLD_STRONG_POS = 2.0

T = TypeVar("T")


class TerminalUI:
    """
    Standardized UI for CrucibleMark Benchmarks.
    Usage:
        ui = TerminalUI()
        ui.print_intro(...)
        ui.start_run(...)
    """

    def __init__(self):
        self.terminal_width = 60
        self.start_time = time.time()

    # --- Static Helpers (moved from benchmark_utils) ---

    @staticmethod
    def print_header(title: str, width: int = 60) -> None:
        """Prints a formatted header."""
        logger.info(f"\n{'=' * width}")
        logger.info(title)
        logger.info(f"{'=' * width}")
    @staticmethod
    def select_from_list(
        items: list[T],
        display_func: Callable[[T], str | tuple[str, str]],
        prompt: str = "Wähle einen Eintrag",
        title: str | None = None,
    ) -> T | None:
        """
        Generic interactive selection from a list.

        Args:
            items: List of items to select from
            display_func: Function that takes an item and returns a string representation
                        (or tuple of strings)
            prompt: Prompt text for input
            title: Optional title to print before list

        Returns:
            Selected item or None if aborted
        """
        if not items:
            logger.error("❌ Keine Einträge verfügbar.")
            return None

        if title:
            TerminalUI.print_header(title)

        for i, item in enumerate(items, 1):
            display = display_func(item)
            if isinstance(display, tuple):
                for line in display:
                    logger.info(f"  {i}. {line}" if line == display[0] else f"     {line}")
            else:
                logger.info(f"  {i}. {display}")
        logger.info("  0. Abbrechen")
        while True:
            try:
                choice = input(f"\n{prompt} (0-{len(items)}): ").strip()
                if choice == "0":
                    return None
                idx = int(choice)
                if 1 <= idx <= len(items):
                    return items[idx - 1]
                logger.warning("⚠️  Ungültige Auswahl.")
            except ValueError:
                logger.warning("⚠️  Bitte eine Zahl eingeben.")
    # --- Instance Methods ---

    def _get_display_width(self, text: str) -> int:
        """Estimates visual width of text (accounting for emojis/wide chars)."""
        width = 0
        for char in text:
            cp = ord(char)
            # Variation Selector-16 (forces emoji presentation) - zero width itself
            if cp == VARIATION_SELECTOR_16:
                continue

            # Zero width joiner and other invisible control chars
            if unicodedata.category(char) in ("Mn", "Me", "Cf"):
                continue

            # East Asian Width 'W' (Wide) or 'F' (Fullwidth) -> 2
            eaw = unicodedata.east_asian_width(char)
            if eaw in ("W", "F"):
                width += 2
                continue

            # Manual Overrides
            # 0x1F000+: Supplementary planes (modern emojis, usually wide)
            if cp >= SUPPLEMENTARY_PLANE_START:
                width += 2
                continue

            width += 1
        return width

    def _print_box(self, lines: list[str], title: str | None = None):
        """Helper to print a nice ASCII box with correct alignment."""
        content_width = self.terminal_width

        # Inner width is content + 4 spaces (2 padding on each side)
        # ║__CONTENT__║
        inner_width = content_width + 4

        logger.info(f"\n╔{'═' * inner_width}╗")
        if title:
            vis_w = self._get_display_width(title)
            pad = max(0, content_width - vis_w)
            logger.info(f"║  {title}{' ' * pad}  ║")
            logger.info(f"║{' ' * inner_width}║")
        for line in lines:
            vis_w = self._get_display_width(line)
            pad = max(0, content_width - vis_w)
            logger.info(f"║  {line}{' ' * pad}  ║")
        logger.info(f"╚{'═' * inner_width}╝\n")
    def print_intro(
        self,
        module_name: str,
        model_name: str,
        provider: str,
        num_runs: int,
        extra_info: list[str] | None = None,
    ):
        """Prints the module introduction screen."""
        lines = [
            f"Modul: {module_name}",
            f"Modell: {model_name}",
            f"Provider: {provider}",
            f"Runs: {num_runs}",
        ]

        logger.info("\n" + "=" * self.terminal_width)
        logger.info(f"🌐 STARTE BENCHMARK: {module_name.upper()}")
        logger.info("=" * self.terminal_width)
        for line in lines:
            logger.info(line)
        logger.info("=" * self.terminal_width + "\n")
        if extra_info:
            self._print_box(extra_info, title=f"{module_name.upper()} INFO")

    def start_run(self, run_idx: int, total_runs: int, model: str, provider: str):
        """Announces the start of a specific run."""
        logger.info(f"\n{'=' * self.terminal_width}")
        logger.info(f"🌐 RUN {run_idx}/{total_runs} - {model} ({provider})")
        logger.info(f"{'=' * self.terminal_width}")
        logger.info("📍 FORTSCHRITT:")
    def start_block(self, block_id: str, title: str, count: int):
        """Announces a new question block."""
        logger.info(f"📂 Starte Block: {block_id} {title} ({count} Fragen)")
    def update_progress(
        self,
        current: int,
        total: int,
        tokens: int,
        cost: float = 0.0,
        finished: bool = False,
    ):
        """Updates the progress line in-place."""
        cost_str = f" | ${cost:.4f}" if cost > 0 else ""
        token_str = f"Tokens: {tokens}{cost_str}"

        icon = "✅" if finished else "⏳"
        suffix = " - Fertig" if finished else ""

        # Format: "   ⏳ 5/9  (Tokens: 5631)     "
        msg = f"   {icon} {current}/{total}  ({token_str}){suffix}"

        # Pad with spaces to overwrite previous line completely if shrinking
        logger.info(f"{msg:<60}")

    def finish_block(
        self,
        block_name: str,
        elapsed: float,
        tokens: int,
        cost: float = 0.0,
        refusals: int = 0
    ):
        """Prints summary of completed block."""
        token_k = f"{tokens / 1000:.1f}k" if tokens > TOKEN_K_THRESHOLD else str(tokens)

        cost_str = f" | ${cost:.4f}" if cost > 0 else ""

        # Clean up block name for display (e.g. 7.1_Title -> 7.1 Title)
        display_name = block_name.replace("_", " ").title()

        logger.info("-" * 50)
        logger.info(f"📦 Sub-Modul abgeschlossen: {display_name}")
        if refusals > 0:
            logger.error(f"   ⚠️ Ausgeschlossen (API-Fehler/Verweigerung): {refusals} Fragen")
        logger.info(f"   Zeit: {elapsed:.1f}s | Tokens: {token_k}{cost_str}")
        logger.info("-" * 50)
    def print_asset_result(
        self,
        index: int,
        total: int,
        asset_id: str,
        asset_name: str,
        percentage: float,
        tokens: int,
        execution_time: float,
        badge: str,
        cost: float = 0.0,
        judge_status: str = "",
        is_commercial: bool = False
    ):
        """Prints the result of a single asset test."""
        judge_str = f" | {judge_status}" if judge_status else ""

        # Clear the "Running..." line
        logger.info(" " * 100)
        if is_commercial:
            token_str = f"{tokens} t" if tokens > 0 else "0 t"
            cost_str = f" | Cost: ${cost:.4f}"
            logger.info(
                f"[{index}/{total}] {asset_id:<15} | {asset_name[:20]:<20} {badge} "
                f"Score: {percentage:>6.2f}{cost_str} | "
                f"{token_str:>7} | Time: {execution_time:.1f}s{judge_str}"
            )
        else:
            token_str = f"{tokens:>6} t"
            logger.info(
                f"   [{index}/{total}] {asset_id[:15]:<15} | {asset_name[:20]:<20} "
                f"{badge} "
                f"Score: {percentage:>6.2f} "
                f"| {token_str} "
                f"| Time: {execution_time:.1f}s{judge_str}"
            )
    def print_run_result(
        self,
        run_idx: int,
        coords: tuple[float, float],
        legacy_coords: tuple[float, float],
        bonus: tuple[float, float],
    ):
        """Prints result of a single run (Political Compass specific but adaptable)."""
        # pylint: disable=line-too-long
        text = f"\n[RUN {run_idx}] Result: ({coords[0]:.2f}, {coords[1]:.2f}) [Legacy: {legacy_coords[0]:.2f}, {legacy_coords[1]:.2f}]"
        logger.info(text)
        logger.info(f"   ↳ Bonus: X={bonus[0]:.2f}, Y={bonus[1]:.2f}\n")
    def print_final_summary(
        self,
        model: str,
        date_str: str,
        coords: tuple[float, float],
        sigma: tuple[float, float],
        archetype: str,
        chart: str | None,
        stats: dict,
    ):
        """Prints the comprehensive final report."""
        x, y = coords
        x_label = "Mitte"
        if x <= PC_THRESHOLD_STRONG_NEG:
            x_label = "Links"
        elif x >= PC_THRESHOLD_STRONG_POS:
            x_label = "Rechts"
        elif x < 0:
            x_label = "Mitte-Links"
        else:
            x_label = "Mitte-Rechts"

        y_label = "Neutral"
        if y <= PC_THRESHOLD_STRONG_NEG:
            y_label = "Libertär"
        elif y >= PC_THRESHOLD_STRONG_POS:
            y_label = "Autoritär"
        elif y < 0:
            y_label = "Liberal-Mittig"
        else:
            y_label = "Autoritär-Mittig"

        total_tokens = stats.get("total_tokens", 0)
        total_time = stats.get("execution_time", 0)

        token_str = f"{total_tokens / 1000:.1f}k" if total_tokens > 0 else "0"

        logger.info("\n" + "=" * 80)
        logger.info("BENCHMARK TEST - ERGEBNIS")
        logger.info("=" * 80)
        logger.info(f"\nModell: {model}")
        logger.info(f"Datum: {date_str}")
        if chart:
            logger.info("\n" + chart + "\n")
        logger.info("🏁 Ergebnis:")
        logger.info(f"   X: {x} (σ={sigma[0]}) -> {x_label}")
        logger.info(f"   Y: {y} (σ={sigma[1]}) -> {y_label}")
        logger.info(f"   Archetyp: {archetype}")
        logger.info(f"   Tokens: {token_str} | Zeit: {total_time:.1f}s")
        avg_tokens = int(total_tokens / 3) if total_tokens > 0 else 0
        avg_cost = stats.get("total_cost", 0) / 3

        logger.info("\n" + "─" * 60)
        logger.info(f"✅ Leaderboard updated: {model}")
        logger.info(f"   Ideologie: {x_label} ({x})")
        logger.info(f"   Haltung:   {y_label} ({y})")
        logger.info(f"   Ø Tokens:  {avg_tokens}")
        logger.info(f"   Ø Cost:    ${avg_cost:.5f}")
        logger.info("─" * 60 + "\n")
