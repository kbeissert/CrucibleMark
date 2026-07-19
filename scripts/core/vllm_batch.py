"""
vLLM-Batch-Orchestrierung für benchmark_auto.py.

Strukturell spiegelbildlich zu scripts/core/llamacpp_batch.py, jedoch nur für
Provider mit ``api_type == "vllm"`` (heute: ``vllm_spark``). Beide Pipelines
teilen sich die Cache-Helper (``get_startable_assets``, ``canonical_lookup_keys``,
``get_existing_results``) — diese bleiben in ``llamacpp_batch.py`` als
Single-Source-of-Truth, damit keine doppelte Cache-Logik entsteht.

Lifecycle-Achsen:
  1. Provider-Discovery (api_type=vllm)
  2. Prophylaktischer Stop + Start/Stop pro Modell + End-of-Batch Cleanup
  3. Context-Manager für Batch-Sessions (Exception-safe Server-Teardown)

Hinweis zu vllm-start-Constraint: ``swap_model()`` wird NICHT verwendet.
Per CLAUDE.md ist ``vllm-start`` nicht idempotent — Server wird zwischen
Modellen immer gestoppt und frisch gestartet.
"""
import logging
import subprocess
import time
from contextlib import contextmanager
from typing import Any
from collections.abc import Generator

logger = logging.getLogger(__name__)

# Konstante für Socket-Release-Zeit nach Server-Stop.
# Konservativ auf 3 s gesetzt (gleicher Default wie llama.cpp). Falls die
# Empirik an asusGX10 zeigt, dass vllm-stop länger braucht, hier erhöhen.
# Wird sowohl im prophylaktischen Stop als auch pro-Modell in der Session
# angewendet, damit der Docker-Container auf der Remote-Box den Port
# freigibt, bevor der nächste vllm-start läuft (Nonidempotenz-Constraint).
VLLM_STOP_SETTLE_SEC: int = 3

# Registrierte vLLM-Provider-Keys. MUSS synchron gehalten werden mit
# utils/providers/<name>.py (PROVIDER_NAMES) und config/provider_config.yaml
# (api_type: vllm). Neue vLLM-Provider müssen hier ergänzt werden —
# get_enabled_vllm_providers validiert per Warning+Skip, dass jeder entdeckte
# Key hier registriert ist, sonst ist _is_local_server_provider False und der
# Score-Delegate-Skip sowie das Cleanup-Flag brechen.
VLLM_PROVIDER_KEYS: frozenset[str] = frozenset({"vllm_spark"})


# =============================================================================
# EXCEPTIONS
# =============================================================================

class VllmSessionError(Exception):
    """Fehler beim Starten oder Verwalten einer vLLM-Server-Session."""


# =============================================================================
# EBENE 1: Lifecycle-Helper
# =============================================================================

def is_vllm_provider(provider_key: str) -> bool:
    """Returns True for local vLLM-style provider keys.

    Quelle der Wahrheit: ``VLLM_PROVIDER_KEYS``. Neue vLLM-Provider (z.B.
    weitere Remote-Boxen) müssen dort ergänzt werden — kein generischer
    ``api_type``-Match, weil der Provider-Client-Registry-Pfad
    (utils/providers/<name>.py) explizit sein muss. ``get_enabled_vllm_providers``
    stellt per Validierung sicher, dass beide Stellen synchron bleiben.
    """
    return provider_key in VLLM_PROVIDER_KEYS


def get_enabled_vllm_providers(config: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Returns enabled local vLLM-style providers in config order.

    Validiert, dass jeder via ``api_type == "vllm"`` entdeckte Provider-Key
    auch in ``VLLM_PROVIDER_KEYS`` registriert ist. Bei Mismatch (Config hat
    einen neuen vLLM-Provider, der noch nicht im Code registriert ist) wird
    eine Warnung geloggt und der Provider übersprungen — verhindert
    silent-breakage von ``_is_local_server_provider``.
    """
    local_cfg = config.get("providers", {}).get("local", {})
    enabled: list[tuple[str, dict[str, Any]]] = []
    for provider_key, provider_cfg in local_cfg.items():
        if not isinstance(provider_cfg, dict):
            continue
        if provider_cfg.get("api_type") != "vllm":
            continue
        if not provider_cfg.get("enabled", False):
            continue
        if provider_key not in VLLM_PROVIDER_KEYS:
            logger.warning(
                "Provider '%s' hat api_type=vllm, ist aber nicht in "
                "VLLM_PROVIDER_KEYS registriert — übersprungen. Bitte "
                "VLLM_PROVIDER_KEYS in scripts/core/vllm_batch.py ergänzen.",
                provider_key,
            )
            continue
        enabled.append((provider_key, provider_cfg))
    return enabled


def set_vllm_provider_context(client: Any, provider_key: str) -> None:
    """Configures the vLLM client instance for the requested provider key.

    VllmBaseClient hat heute keinen ``_set_provider_context``-Hook (anders als
    LlamaCppBaseClient — dort wird ein Auth-Header basierend auf dem
    Provider-Key umgeschaltet). Wir rufen den Setter nur auf, falls er
    existiert; sonst ist der Aufruf ein No-op und wir verlassen uns auf den
    Provider-Subklassen-Registry-Pfad, der pro Klasse eindeutig ist.
    """
    setter = getattr(client, "_set_provider_context", None)
    if callable(setter):
        setter(provider_key)


def stop_vllm_provider_server(
    config: dict[str, Any],
    provider_key: str | None = None,
) -> None:
    """Stops vLLM server(s) - prophylactic or specific provider.

    Bewusst getrennt von ``stop_llamacpp_provider_server``: ein gemeinsames
    Run-Skript (``pkill -f 'vllm|llama-server'``) würde Treffer auf
    falsche Prozesse riskieren, falls beide Provider-Typen parallel laufen.

    Args:
        config: Vollständige Config (für Provider-Lookup)
        provider_key: Optional - nur diesen Provider stoppen
    """
    enabled_vllm = get_enabled_vllm_providers(config)
    if not enabled_vllm:
        return

    if provider_key is not None:
        enabled_vllm = [(k, v) for k, v in enabled_vllm if k == provider_key]
        if not enabled_vllm:
            return

    print("   🧹 Stoppe laufende vLLM-Server (prophylaktisch) ...")
    seen_cmds: set[str] = set()
    for _pkey, provider_cfg in enabled_vllm:
        # server_stop_cmd ist Pflicht für vLLM-Provider (SSH-Remote-Skript).
        # Kein Default — ein lokales "vllm-stop" gäbe es auf dem Orchestrator-
        # Host nicht und capture_output würde den Fehler verschlucken.
        stop_cmd = str(provider_cfg.get("server_stop_cmd", "")).strip()
        if not stop_cmd:
            logger.warning(
                "Provider '%s' hat kein server_stop_cmd — prophylaktischer "
                "Stop übersprungen.", _pkey,
            )
            continue
        if stop_cmd in seen_cmds:
            continue
        seen_cmds.add(stop_cmd)
        # Defense-in-Depth: vllm-stop verlangt --yes in nicht-interaktiven
        # Umgebungen, sonst stiller Fehlschlag. Auto-Inject analog zum
        # Connector (utils/providers/vllm_base.py:_server_stop_cmd).
        if "vllm-stop" in stop_cmd and "--yes" not in stop_cmd:
            stop_cmd = stop_cmd.rstrip() + " --yes"
        subprocess.run(stop_cmd, shell=True, check=False, capture_output=True)

    time.sleep(VLLM_STOP_SETTLE_SEC)


def run_vllm_provider_cleanup(provider_key: str, provider_cfg: dict[str, Any]) -> None:
    """Führt End-of-Batch Cleanup für einen vLLM-Provider aus.

    Identische Semantik wie ``run_llamacpp_provider_cleanup``: liest
    ``server_post_stop_cmd`` aus der Provider-Config und führt es aus,
    sofern ``cleanup_on_exit: true`` gesetzt ist. Im Fehlerfall wird
    geloggt, aber keine Exception hochgereicht (Cleanup darf den
    Batch-Abschluss nicht verhindern).
    """
    if not provider_cfg.get("cleanup_on_exit", False):
        return

    post_stop_cmd = provider_cfg.get("server_post_stop_cmd")
    if not post_stop_cmd:
        return

    print(f"   🧹 Post-Stop Cleanup für '{provider_key}' ...")
    try:
        subprocess.run(post_stop_cmd, shell=True, check=False)
    except Exception as exc:  # noqa: BLE001
        # Cleanup-Fehler dürfen den Batch-Abschluss nicht verhindern
        # (dokumentierte Invariante, parallel zu run_llamacpp_provider_cleanup).
        # Breit gefasst, damit auch unexpected Exceptions (TypeError etc.)
        # nicht den Batch abbrechen.
        print(f"   ⚠️ Post-Stop Cleanup fehlgeschlagen: {exc}")


# =============================================================================
# EBENE 2: Context-Manager (Exception-safe Server-Teardown)
# =============================================================================

@contextmanager
def vllm_model_session(
    runner: Any,  # UnifiedBenchmarkRunner
    provider_key: str,
    model_id: str,
) -> Generator[Any, None, None]:
    """Context-Manager für eine vLLM-Modell-Session mit automatischem Server-Stop.

    Stellt sicher, dass der Server nach der Verwendung immer gestoppt wird,
    auch bei Exceptions oder KeyboardInterrupt. Pro-Modell aufrufen —
    ``stop_server()`` zwischen Modellen ist Pflicht (CLAUDE.md:
    vllm-start ist nicht idempotent).

    Cleanup (``server_post_stop_cmd``) ist bewusst NICHT Teil der Session —
    es ist Batch-Ende-Verantwortung des Orchestrators
    (``run_vllm_provider_cleanup``), nicht der einzelnen Modell-Session.

    Raises:
        VllmSessionError: Wenn der Server nicht gestartet werden kann
            oder der Client nicht im Registry gefunden wird.

    Usage:
        for model_id in model_ids:
            try:
                with vllm_model_session(runner, provider_key, model_id) as client:
                    _run_vllm_model_modules(...)
            except VllmSessionError as e:
                print(f"   ❌ {e} — überspringe Modell.")
                continue

    Args:
        runner: UnifiedBenchmarkRunner-Instanz
        provider_key: z.B. "vllm_spark"
        model_id: Modell-ID aus provider_config.yaml

    Yields:
        VllmSparkClient-Instanz (oder jeweilige vLLM-Subklasse)
    """
    vllm_client = runner.client.clients.get(provider_key)
    if vllm_client is None:
        raise VllmSessionError(
            f"VllmClient '{provider_key}' nicht im Client-Registry gefunden."
        )

    set_vllm_provider_context(vllm_client, provider_key)

    # Server starten — Per CLAUDE.md nicht idempotent, daher nie swap_model()
    if not vllm_client.start_server(model_id):
        raise VllmSessionError(
            f"vLLM-Server für '{model_id}' konnte nicht gestartet werden."
        )

    try:
        yield vllm_client
    finally:
        print("\n   🛑 Stoppe vLLM Server...")
        vllm_client.stop_server()
        # Settle: Docker-Container auf der Remote-Box braucht Zeit, um den
        # Port freizugeben. Ohne Settle schlägt der nächste vllm-start fehl
        # (Nonidempotenz-Constraint, siehe CLAUDE.md).
        time.sleep(VLLM_STOP_SETTLE_SEC)
