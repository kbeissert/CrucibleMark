"""Module for formatters.py."""
from benchmark_modules.cli_benchmark.core.constants import (
    BIG_TOKEN_THRESHOLD,
    INLINE_GREEN,
    INLINE_ORANGE,
    INLINE_STAR,
    INLINE_TROPHY,
    INLINE_YELLOW,
)


class CLITerminalFormatter:
    """Isoliert alle Konsolenausgaben und Formatierungen für das CLI-Modul."""

    @staticmethod
    def get_score_badge(pct: float) -> str:
        """Get formatted badge."""
        if pct >= INLINE_TROPHY:
            return "🏆"
        if pct >= INLINE_STAR:
            return "⭐"
        if pct >= INLINE_GREEN:
            return "🟢"
        if pct >= INLINE_YELLOW:
            return "🟡"
        if pct >= INLINE_ORANGE:
            return "🟠"
        return "🔴"

    @staticmethod
    def format_tokens(tokens: int) -> str:
        """Format tokens."""
        if tokens > BIG_TOKEN_THRESHOLD:
            return f"{tokens / 1000.0:.1f}k T"
        return f"{tokens} T"

    @staticmethod
    def print_loading(idx: int, total: int, name: str) -> None:
        """Print loading."""
        print(f"   ⏳ [{idx}/{total}] {name:<25}: Test läuft...", end="\r", flush=True)

    @staticmethod
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def print_task_result(
        idx: int,
        total: int,
        name: str,
        status: str | None,
        pct: float,
        tokens: int,
        time_s: float,
    ) -> None:
        """Print task result."""
        badge = CLITerminalFormatter.get_score_badge(pct)
        token_str = CLITerminalFormatter.format_tokens(tokens)
        status_icon = "✓" if status == "success" else "✗"

        print(" " * 80, end="\r")
        print(
            f"   {status_icon} [{idx}/{total}] {name:<25}: "
            f"{pct:>5.1f}% {badge} | {token_str} | {time_s:>4.1f}s"
        )
