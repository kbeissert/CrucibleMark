"""
update_prices.py
----------------
Erzwingt eine Aktualisierung des LiteLLM-Preis-Caches, unabhängig von der TTL.
Verwendung: make update-prices
"""
import logging
import sys
from pathlib import Path

# Projektroot in sys.path aufnehmen (Aufruf aus Makefile via .venv/bin/python)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logging.basicConfig(level=logging.INFO, format="%(message)s")

from utils.pricing_updater import PricingUpdater, CACHE_PATH

p = PricingUpdater()

print("💱 Preis-Cache vor Update:", p.get_cache_age_str())

# Cache-Datei löschen, damit ensure_fresh() einen echten Fetch auslöst
if CACHE_PATH.exists():
    CACHE_PATH.unlink()
p._prices = None

updated = p.ensure_fresh()
if updated:
    print(p.get_status_line())
    sys.exit(0)
else:
    print("❌ Update fehlgeschlagen – ist eine Internetverbindung vorhanden?")
    sys.exit(1)
