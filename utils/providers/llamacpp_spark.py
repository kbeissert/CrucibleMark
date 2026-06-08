"""
llama.cpp-Provider für DGX Spark (NVIDIA CUDA, Remote via SSH).

Hardware-Kontext:
    DGX Spark: ~128 GB unified memory, davon ~120 GB für Modell + Kontext nutzbar.
    Bei Context=65536 und parallel=4 bleiben pro Slot ~16K Tokens reservierter Kontext,
    was ausreichend ist für 30B-40B MoE-Modelle (Q4-Q8) mit Thinking-Ausgaben.
    Server-Start nach Refactoring (llamacpp_batch.py) deutlich schneller: Timeout von 420s → 180s.

Steuerung erfolgt per SSH vom Benchmark-Host.
GGUF-Pfad: /home/kay_beissert/ai/models/llm/gguf/
Port 1235 wird für den Benchmark-Server genutzt.

Seit Phase 19 (2026-06-08) getrennte Klasse statt Runtime-Switch
in `LlamaCppClient`. Eliminiert die Bug-Klasse "falsche Provider-Config
durch vergessene `_set_provider_context()`-Aufrufe" strukturell.
"""
import logging

from utils.providers.llamacpp_base import LlamaCppBaseClient

logger = logging.getLogger(__name__)


class LlamaCppSparkClient(LlamaCppBaseClient):
    """Provider-Client für llama.cpp auf DGX Spark (Remote via SSH, NVIDIA CUDA).

    Konfig-Key: `providers.local.llamacpp_spark` in `provider_config.yaml`.
    Bindet sich automatisch über `PROVIDER_NAMES` ins Auto-Registry
    (`BaseProviderClient._registry["llamacpp_spark"]`).
    """

    # Auto-Registry: bindet diese Klasse an genau einen Provider-Key.
    # Keine Aliase — der Config-Key ist eindeutig.
    PROVIDER_NAMES = ["llamacpp_spark"]

    # Konfigurations-Lookup: `providers.local[_PROVIDER_KEY]`.
    _PROVIDER_KEY = "llamacpp_spark"
