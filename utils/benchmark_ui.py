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
import sys
import unicodedata
from typing import Optional, List, TypeVar, Callable

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
        print(f"\n{'=' * width}")
        print(title)
        print(f"{'=' * width}")

    @staticmethod
    def select_from_list(
        items: List[T],
        display_func: Callable[[T], str | tuple[str, str]],
        prompt: str = "Wähle einen Eintrag",
        title: Optional[str] = None,
    ) -> Optional[T]:
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
            print("❌ Keine Einträge verfügbar.")
            return None

        if title:
            TerminalUI.print_header(title)

        for i, item in enumerate(items, 1):
            display = display_func(item)
            if isinstance(display, tuple):
                for line in display:
                    print(f"  {i}. {line}" if line == display[0] else f"     {line}")
            else:
                print(f"  {i}. {display}")

        print("  0. Abbrechen")

        while True:
            try:
                choice = input(f"\n{prompt} (0-{len(items)}): ").strip()
                if choice == "0":
                    return None
                idx = int(choice)
                if 1 <= idx <= len(items):
                    return items[idx - 1]
                print("⚠️  Ungültige Auswahl.")
            except ValueError:
                print("⚠️  Bitte eine Zahl eingeben.")

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

    def _print_box(self, lines: list[str], title: Optional[str] = None):
        """Helper to print a nice ASCII box with correct alignment."""
        content_width = self.terminal_width

        # Inner width is content + 4 spaces (2 padding on each side)
        # ║__CONTENT__║
        inner_width = content_width + 4

        print(f"\n╔{'═' * inner_width}╗")

        if title:
            vis_w = self._get_display_width(title)
            pad = max(0, content_width - vis_w)
            print(f"║  {title}{' ' * pad}  ║")
            print(f"║{' ' * inner_width}║")

        for line in lines:
            vis_w = self._get_display_width(line)
            pad = max(0, content_width - vis_w)
            print(f"║  {line}{' ' * pad}  ║")

        print(f"╚{'═' * inner_width}╝\n")

    def print_intro(
        self,
        module_name: str,
        model_name: str,
        provider: str,
        num_runs: int,
        extra_info: Optional[list[str]] = None,
    ):
        """Prints the module introduction screen."""
        lines = [
            f"Modul: {module_name}",
            f"Modell: {model_name}",
            f"Provider: {provider}",
            f"Runs: {num_runs}",
        ]

        print("\n" + "=" * self.terminal_width)
        print(f"🌐 STARTE BENCHMARK: {module_name.upper()}")
        print("=" * self.terminal_width)
        for line in lines:
            print(line)
        print("=" * self.terminal_width + "\n")

        if extra_info:
            self._print_box(extra_info, title=f"{module_name.upper()} INFO")

    def start_run(self, run_idx: int, total_runs: int, model: str, provider: str):
        """Announces the start of a specific run."""
        print(f"\n{'=' * self.terminal_width}")
        print(f"🌐 RUN {run_idx}/{total_runs} - {model} ({provider})")
        print(f"{'=' * self.terminal_width}")
        print("📍 FORTSCHRITT:")

    def start_block(self, block_id: str, title: str, count: int):
        """Announces a new question block."""
        print(f"📂 Starte Block: {block_id} {title} ({count} Fragen)")

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
        end_char = "\n" if finished else "\r"

        # Format: "   ⏳ 5/9  (Tokens: 5631)     "
        msg = f"   {icon} {current}/{total}  ({token_str}){suffix}"

        # Pad with spaces to overwrite previous line completely if shrinking
        print(f"{msg:<60}", end=end_char)
        if not finished:
            sys.stdout.flush()

    def finish_block(
        self, block_name: str, elapsed: float, tokens: int, cost: float = 0.0
    ):
        """Prints summary of completed block."""
        if tokens > TOKEN_K_THRESHOLD:
            token_k = f"{tokens / 1000:.1f}k"
        else:
            token_k = str(tokens)

        cost_str = f" | ${cost:.4f}" if cost > 0 else ""

        # Clean up block name for display (e.g. 7.1_Title -> 7.1 Title)
        display_name = block_name.replace("_", " ").title()

        print("-" * 50)
        print(f"📦 Sub-Modul abgeschlossen: {display_name}")
        print(f"   Zeit: {elapsed:.1f}s | Tokens: {token_k}{cost_str}")
        print("-" * 50)

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
        print(text)
        print(f"   ↳ Bonus: X={bonus[0]:.2f}, Y={bonus[1]:.2f}\n")

    def print_final_summary(
        self,
        model: str,
        date_str: str,
        coords: tuple[float, float],
        sigma: tuple[float, float],
        archetype: str,
        chart: Optional[str],
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

        print("\n" + "=" * 80)
        print("BENCHMARK TEST - ERGEBNIS")
        print("=" * 80)
        print(f"\nModell: {model}")
        print(f"Datum: {date_str}")

        if chart:
            print("\n" + chart + "\n")

        print("🏁 Ergebnis:")
        print(f"   X: {x} (σ={sigma[0]}) -> {x_label}")
        print(f"   Y: {y} (σ={sigma[1]}) -> {y_label}")
        print(f"   Archetyp: {archetype}")
        print(f"   Tokens: {token_str} | Zeit: {total_time:.1f}s")

        avg_tokens = int(total_tokens / 3) if total_tokens > 0 else 0
        avg_cost = stats.get("total_cost", 0) / 3

        print("\n" + "─" * 60)
        print(f"✅ Leaderboard updated: {model}")
        print(f"   Ideologie: {x_label} ({x})")
        print(f"   Haltung:   {y_label} ({y})")
        print(f"   Ø Tokens:  {avg_tokens}")
        print(f"   Ø Cost:    ${avg_cost:.5f}")
        print("─" * 60 + "\n")
