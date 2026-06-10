"""
llama.cpp-Provider für lokale MacBook-Hardware (M4).

Hardware-Kontext:
    MacBook Pro (M4 Max): ~16-18 GB nutzbarer VRAM für Modell + Kontext.
    Bei Context=32000 und parallel=4 bleiben pro Slot ~4K Tokens reservierter Kontext,
    was für Puffer + KV-Cache bei 12B-14B Modellen (Q4-Q6) ausreichend ist.

Jedes Modell wird explizit in config/provider_config.yaml unter
`providers.local.llamacpp.models` eingetragen:

  - id:            API-Bezeichner (wird an /v1/chat/completions als `model` übergeben)
  - model_file:    GGUF-Dateiname relativ zu `model_dir`
  - context_length: optionales Überschreiben des globalen Kontextfensters
  - n_gpu_layers:  GPU-Offload-Schichten (0 = reiner CPU-Betrieb)

Der Client baut daraus automatisch den vollständigen `llama-server`-Befehl
(inkl. --alias, --ctx-size, --n-gpu-layers) und swappt das Modell beim Wechsel.

Sampling-Defaults: SSoT ist `providers.local.config.llama_cpp_defaults` in
provider_config.yaml (temperature=0.6, top_p=0.95, top_k=40, seed=42).
"""

import logging

from utils.providers.llamacpp_base import LlamaCppBaseClient

logger = logging.getLogger(__name__)


class LlamaCppLocalClient(LlamaCppBaseClient):
    """Provider-Client für llama.cpp auf M4 MacBook Pro (lokal, OpenAI-kompatible API).

    Konfig-Key: `providers.local.llamacpp` in `provider_config.yaml`.
    Bindet sich automatisch über `PROVIDER_NAMES` ins Auto-Registry
    (`BaseProviderClient._registry["llamacpp"]`).
    """

    # Auto-Registry: bindet diese Klasse an die Provider-Keys.
    # Aliase `llama_cpp` und `llamacpp_local` sind entfallen (Phase 19) —
    # das vereinfacht Konfig-Lookup und eliminiert Switch-Bugs.
    PROVIDER_NAMES = ["llamacpp"]

    # Konfigurations-Lookup: `providers.local[_PROVIDER_KEY]`.
    _PROVIDER_KEY = "llamacpp"
