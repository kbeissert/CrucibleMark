"""
vLLM-Provider für asusGX10 (NVIDIA Blackwell, Remote via SSH).

Hardware-Kontext:
    asusGX10: eigenständige Workstation mit NVIDIA GB10 (Blackwell).
    Steuerung erfolgt per SSH vom Benchmark-Host.
    Default-Port 4300/v1, Modelle können bis zu 600 s für das Laden
    benötigen (große MoE-Modelle).

Server-Lifecycle:
    Gestartet/gestoppt über die Skripte ``vllm-start`` und ``vllm-stop``
    im Remote-PATH. ``vllm-start`` nimmt ``--config <NAME|PATH>``
    entgegen und entscheidet anhand der TOML in
    ``~/ai/shared/configs/vllm/models/`` welches Modell mit welchen
    Server-Parametern (Context, Quantisierung, MoE-Backend) geladen
    wird. ``--gpu-mem <0.01-1.0>`` ist eine reine Ressourcen-Override
    und verändert keine Modell-Parameter.

Seit 2026-07-06 getrennte Klasse statt Runtime-Switch in
``VllmClient``. Eliminiert die Bug-Klasse "falsche Provider-Config
durch vergessene ``_set_provider_context()``-Aufrufe" strukturell
(Pattern konsistent mit llamacpp_base/llamacpp_spark aus Phase 19).
"""
import logging

from utils.providers.vllm_base import VllmBaseClient

logger = logging.getLogger(__name__)


class VllmSparkClient(VllmBaseClient):
    """Provider-Client für vLLM auf asusGX10 (Remote via SSH, NVIDIA Blackwell).

    Konfig-Key: ``providers.local.vllm_spark`` in ``provider_config.yaml``.
    Bindet sich automatisch über ``PROVIDER_NAMES`` ins Auto-Registry
    (``BaseProviderClient._registry["vllm_spark"]``).
    """

    # Auto-Registry: bindet diese Klasse an genau einen Provider-Key.
    # Keine Aliase — der Config-Key ist eindeutig.
    PROVIDER_NAMES = ["vllm_spark"]

    # Konfigurations-Lookup: ``providers.local[_PROVIDER_KEY]``.
    _PROVIDER_KEY = "vllm_spark"
