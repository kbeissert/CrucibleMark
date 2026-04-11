"""
pricing_updater.py
------------------
Holt aktuelle Tokenpreise von der LiteLLM Pricing DB (Community-gepflegt,
typischerweise innerhalb 1-2 Tagen nach Provider-Ankündigungen aktualisiert).

Wird automatisch ausgelöst wenn:
  - Ein kommerzieller Benchmark gestartet wird (via CostTracker.__init__)
  - `make analyze-costs` ausgeführt wird (selber Pfad)

TTL-Empfehlung: 7 Tage
  Preisänderungen von Anthropic/OpenAI/Mistral sind selten (2-4x/Jahr).
  7 Tage = maximale Abweichung eine Woche, kein täglicher Netzwerk-Overhead.
  Kann via cost_limits.yaml settings.pricing_ttl_days überschrieben werden.

Cache-Datei: config/.prices_cache.json (machine-generated, nicht committen)
Fallback:    config/cost_limits.yaml (manuelle Overrides + Budgets)
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.error import URLError
from urllib.request import urlopen
from utils.constants import TIMEOUT_HTTP_FETCH

logger = logging.getLogger(__name__)

LITELLM_PRICING_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/"
    "model_prices_and_context_window.json"
)
"""Fallback-URL falls cost_limits.yaml noch nicht geladen ist."""

CACHE_PATH = Path("config/.prices_cache.json")
DEFAULT_TTL_DAYS = 7

COST_LIMITS_PATH = Path("config/cost_limits.yaml")


def _load_pricing_url() -> str:
    """Liest pricing_source_url aus cost_limits.yaml, fällt auf Konstante zurück."""
    try:
        if COST_LIMITS_PATH.exists():
            import yaml  # pylint: disable=import-outside-toplevel

            data = yaml.safe_load(COST_LIMITS_PATH.read_text(encoding="utf-8")) or {}
            url = data.get("settings", {}).get("pricing_source_url", "")
            if url:
                return url
    except Exception as e:
        logger.debug("Konnte pricing_source_url nicht aus Config laden: %s", e)
    return LITELLM_PRICING_URL


# Mapping: CrucibleMark model-ID → LiteLLM-Key in pricing DB.
#
# Nur Modelle eintragen die in LiteLLM vorhanden sind.
# Modelle OHNE Eintrag (z.B. gpt-5, gpt-5-mini) bleiben in cost_limits.yaml
# manuell gepflegt und werden als Fallback verwendet.
LITELLM_MODEL_MAP: Dict[str, str] = {
    # --- Anthropic ---
    "claude-sonnet-4-6": "claude-sonnet-4-6",
    "claude-opus-4-6": "claude-opus-4-6",
    "claude-sonnet-4-5-20250929": "claude-sonnet-4-5-20250929",
    "claude-opus-4-5-20251101": "claude-opus-4-5-20251101",
    "claude-haiku-4-5-20251001": "claude-haiku-4-5-20251001",
    "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20241022": "claude-3-5-sonnet-20241022",
    "claude-3-haiku-20240307": "claude-3-haiku-20240307",
    "claude-3-haiku": "claude-3-haiku-20240307",
    # --- OpenAI ---
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
    "o3-mini": "o3-mini",
    # gpt-5 / gpt-5-mini sind noch nicht in LiteLLM → cost_limits.yaml-Fallback
    # --- Mistral (LiteLLM nutzt Provider-Prefix) ---
    "mistral-large-latest": "mistral/mistral-large-latest",
    "mistral-medium-latest": "mistral/mistral-medium-latest",
    "ministral-8b": "mistral/ministral-8b-latest",
    "ministral-3b": "mistral/ministral-3b-latest",
    # --- xAI (Grok) ---
    "grok-3": "xai/grok-3",
    "grok-3-mini": "xai/grok-3-mini",
    
    
    # --- Google Gemini ---
    "gemini-3.1-pro-preview": "gemini/gemini-3.1-pro-preview",
    "gemini-3-flash-preview": "gemini/gemini-3-flash-preview",
    "gemini-2.5-pro": "gemini/gemini-2.5-pro",
    "gemini-2.5-flash": "gemini/gemini-2.5-flash",
    "gemini-2.5-flash-lite": "gemini/gemini-2.5-flash-lite",
}


class PricingUpdater:
    """
    Verwaltet den lokalen LiteLLM-Preis-Cache.

    Singleton-Pattern: Preis-Daten werden einmal pro Prozess in den Speicher
    geladen. Netzwerk-Requests finden nur statt wenn der Cache veraltet ist.
    """

    _instance: Optional["PricingUpdater"] = None
    _prices: Optional[Dict[str, Dict]] = None

    def __new__(cls) -> "PricingUpdater":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def ensure_fresh(self, ttl_days: int = DEFAULT_TTL_DAYS) -> bool:
        """
        Prüft ob der Cache aktuell ist und aktualisiert ihn bei Bedarf.

        Args:
            ttl_days: Maximales Alter des Caches in Tagen.

        Returns:
            True wenn ein Netzwerk-Update stattgefunden hat, sonst False.
            Schlägt bei Verbindungsfehlern still fehl (kein Programmabbruch).
        """
        if self._is_cache_fresh(ttl_days):
            if self._prices is None:
                self._load_cache()
            return False

        age_str = self.get_cache_age_str()
        logger.info(
            "🔄 Preis-Cache veraltet (%s) – aktualisiere LiteLLM Pricing DB...",
            age_str,
        )
        updated = self._fetch_and_cache()
        if updated:
            entry_count = len(self._prices or {})
            logger.info(
                "✅ Tokenpreise aktualisiert: %d Modelle gecacht (%s)",
                entry_count,
                datetime.now().strftime("%Y-%m-%d %H:%M"),
            )
        else:
            logger.warning(
                "⚠️  Preisupdate fehlgeschlagen – nutze vorhandenen Cache / cost_limits.yaml."
            )
            # Lade alten Cache als Fallback, auch wenn er veraltet ist
            if self._prices is None:
                self._load_cache()
        return updated

    def get_price(self, model_id: str) -> Optional[Tuple[float, float]]:
        """
        Gibt (input_cost_per_1k, output_cost_per_1k) für ein Modell zurück.
        None wenn das Modell nicht im Cache ist.
        """
        if self._prices is None:
            self._load_cache()
        if not self._prices:
            return None

        # 1. Exakter Match
        entry = self._prices.get(model_id)
        if entry:
            return entry["input_cost_per_1k"], entry["output_cost_per_1k"]

        # 2. Prefix-Match (z.B. "claude-sonnet-4-6-xyz" trifft "claude-sonnet-4-6")
        for key, val in self._prices.items():
            if model_id.startswith(key):
                return val["input_cost_per_1k"], val["output_cost_per_1k"]
        return None

    def get_cache_age_str(self) -> str:
        """Gibt das Alter des Caches als lesbaren String zurück."""
        if not CACHE_PATH.exists():
            return "kein Cache vorhanden"
        try:
            data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            fetched = datetime.fromisoformat(data["fetched_at"])
            delta = datetime.now() - fetched
            return (
                f"{delta.days}d {delta.seconds // 3600}h alt"
                f" (Stand: {fetched.strftime('%Y-%m-%d')})"
            )
        except Exception:
            return "unbekannt"

    def get_status_line(self, ttl_days: int = DEFAULT_TTL_DAYS) -> str:
        """Einzeiler für make-Output / Logs."""
        fresh = self._is_cache_fresh(ttl_days)
        age = self.get_cache_age_str()
        icon = "✅" if fresh else "⚠️ "
        return f"{icon} Preise: {age} | TTL: {ttl_days} Tage | Quelle: LiteLLM/BerriAI"

    # ------------------------------------------------------------------ #
    #  Private                                                             #
    # ------------------------------------------------------------------ #

    def _is_cache_fresh(self, ttl_days: int) -> bool:
        if not CACHE_PATH.exists():
            return False
        try:
            data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            fetched = datetime.fromisoformat(data["fetched_at"])
            return datetime.now() - fetched < timedelta(days=ttl_days)
        except Exception:
            return False

    def _load_cache(self):
        if not CACHE_PATH.exists():
            return
        try:
            data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            self._prices = data.get("prices", {})
            logger.debug(
                "Preis-Cache geladen: %d Modelle (Stand: %s)",
                len(self._prices),
                data.get("fetched_at", "?")[:10],
            )
        except Exception as e:
            logger.debug("Preis-Cache konnte nicht geladen werden: %s", e)

    def _fetch_and_cache(self) -> bool:
        url = _load_pricing_url()
        try:
            with urlopen(url, timeout=TIMEOUT_HTTP_FETCH) as resp:
                raw: Dict = json.loads(resp.read().decode("utf-8"))
        except (URLError, OSError, Exception) as e:
            logger.warning("LiteLLM-Preisfetch fehlgeschlagen: %s", e)
            return False

        prices: Dict[str, Dict] = {}
        missing: list[str] = []

        for our_id, litellm_key in LITELLM_MODEL_MAP.items():
            entry = raw.get(litellm_key)
            if not entry:
                missing.append(our_id)
                continue
            inp = entry.get("input_cost_per_token", 0.0) * 1000  # → per 1k
            out = entry.get("output_cost_per_token", 0.0) * 1000
            if inp > 0 or out > 0:
                prices[our_id] = {
                    "input_cost_per_1k": round(inp, 8),
                    "output_cost_per_1k": round(out, 8),
                }

        if missing:
            logger.debug(
                "Folgende Modelle nicht in LiteLLM DB gefunden (cost_limits.yaml-Fallback): %s",
                ", ".join(missing),
            )

        if not prices:
            logger.warning(
                "LiteLLM-Response enthielt keine verwertbaren Preiseinträge."
            )
            return False

        cache = {
            "fetched_at": datetime.now().isoformat(),
            "ttl_days": DEFAULT_TTL_DAYS,
            "source": _load_pricing_url(),
            "model_count": len(prices),
            "prices": prices,
        }
        CACHE_PATH.write_text(
            json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self._prices = prices
        return True
