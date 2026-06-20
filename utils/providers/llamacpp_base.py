"""
Gemeinsame llama.cpp-Logik für lokale Provider-Klassen.

Seit Phase 19 (2026-06-08) ist die frühere Multi-Provider-Klasse
`LlamaCppClient` mit `_provider_name`-Runtime-Switch aufgeteilt in eine
schlanke Basisklasse + zwei Hardware-spezifische Subklassen
(`LlamaCppLocalClient`, `LlamaCppSparkClient`). Damit folgt die
llama.cpp-Integration dem Muster aller anderen Provider
(OllamaClient, OpenRouterClient, …): 1 Klasse pro Hardware-Target,
1 Instanz pro Provider-Key, kein State-Sharing, keine Bug-Klasse mehr
durch vergessene `_set_provider_context()`-Aufrufe.

Elternklasse: `BaseProviderClient` aus `utils/providers/base.py`.
Subklassen MÜSSEN `PROVIDER_NAMES` (für Auto-Registry) und
`_PROVIDER_KEY` (für Config-Lookup) als Klassenattribute setzen.
"""
import json
import logging
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

from utils.model_utils import resolve_token_budget
from utils.providers.base import BaseProviderClient

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


# HTTP-Statuscodes (vermeidet PLR2004 Magic-Value-Warnungen)
HTTP_OK: int = 200


# Default-Sampling-Parameter, die llama.cpp upstream-Defaults entsprechen
# (seed=42 für Reproduzierbarkeit statt llama.cpp-Default 0xFFFFFFFF).
# Reihenfolge: (config-key, cli-flag, hardcoded fallback).
_SAMPLING_PARAMS: tuple[tuple[str, str, float], ...] = (
    ("temperature",      "--temp",             0.8),
    ("top_p",            "--top-p",            0.95),
    ("top_k",            "--top-k",            40),
    ("min_p",            "--min-p",            0.0),
    ("presence_penalty", "--presence-penalty", 0.0),
    ("repeat_penalty",   "--repeat-penalty",   1.0),
)


def _extract_port(base_url: str, default: int = 1235) -> int:
    """Port aus base_url parsen, Fallback auf default bei Parse-Fehler."""
    try:
        return urllib.parse.urlparse(base_url).port or default
    except (ValueError, AttributeError):
        return default


class LlamaCppBaseClient(BaseProviderClient):
    """Provider-agnostische llama.cpp-Logik (Server-Lifecycle, OpenAI-Client, Query-Loop).

    Konkrete Subklassen (z.B. `LlamaCppLocalClient`) binden sich über
    `PROVIDER_NAMES` (Auto-Registry) und `_PROVIDER_KEY` (Config-Lookup)
    an genau einen Eintrag in `providers.local.*` aus `provider_config.yaml`.

    Wichtig: `PROVIDER_NAMES = []` — die Basisklasse registriert sich NICHT
    selbst im Auto-Registry. Sie ist abstrakt in dem Sinne, dass eine
    direkte Instanziierung zu inkorrektem Provider-Lookup führt.
    """

    # Auto-Registry deaktiviert — nur Subklassen registrieren sich.
    PROVIDER_NAMES: list[str] = []

    # Klassenkonstante, die jede Subklasse überschreiben MUSS.
    # Bestimmt den Config-Key unter `providers.local.*`.
    _PROVIDER_KEY: str = ""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        if not self._PROVIDER_KEY:
            raise NotImplementedError(
                f"{type(self).__name__} muss _PROVIDER_KEY als Klassenattribut setzen."
            )
        self._client: Any | None = None
        self._client_base_url: str | None = None
        self._active_model: str | None = None
        self._server_pid: int | None = None

    # ------------------------------------------------------------------
    # Config helpers (provider-key-fest, kein Runtime-Switch)
    # ------------------------------------------------------------------

    @property
    def _local_cfg(self) -> dict[str, Any]:
        """Gecachte Sicht auf `providers.local`."""
        return self.config.get("providers", {}).get("local", {})

    def _provider_cfg(self) -> dict[str, Any]:
        """Provider-Config unter `providers.local[_PROVIDER_KEY]` lesen."""
        provider_cfg = self._local_cfg.get(self._PROVIDER_KEY, {})
        if provider_cfg:
            return provider_cfg
        # Defense-in-Depth: wenn _PROVIDER_KEY fehlt, sauberer leerer Dict
        # statt Fallback auf einen anderen Provider.
        return {}

    def _base_url(self) -> str:
        return self._provider_cfg().get("base_url", "http://127.0.0.1:1235/v1")

    def _api_key(self) -> str:
        return self._provider_cfg().get("api_key", "sk-local")

    def _model_dir(self) -> str:
        return self._provider_cfg().get("model_dir", "~/models")

    def _server_start_cmd(self) -> str:
        return os.path.expanduser(
            self._provider_cfg().get("server_start_cmd", "llama-server")
        )

    def _server_stop_cmd(self) -> str:
        return self._provider_cfg().get("server_stop_cmd", "pkill -f llama-server")

    def _server_root_url(self) -> str:
        """Base URL ohne /v1-Suffix, z. B. http://127.0.0.1:1235."""
        return self._base_url().rstrip("/").removesuffix("/v1")

    def _health_url(self) -> str:
        return f"{self._server_root_url()}/health"

    def _chat_completions_url(self) -> str:
        return f"{self._server_root_url()}/v1/chat/completions"

    # ------------------------------------------------------------------
    # Model name normalization (Card-Canonical vs. Config-ID)
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_model_name(model_id: str | None) -> str:
        """Punkt → Underscore, Bindestrich → Underscore für Vergleich."""
        if not model_id:
            return ""
        return model_id.replace(".", "_").replace("-", "_")

    @staticmethod
    def _strip_model_name(model_id: str) -> str:
        """Nicht-alphanumerische Zeichen entfernen (für Adopt-Pfad)."""
        return model_id.lower().replace(".gguf", "").replace(".", "").replace("-", "").replace("_", "")

    def _model_cfg(self, model_id: str) -> dict[str, Any]:
        """Provider-Models-Config-Lookup mit Defense-in-Depth für ID-Varianten.

        Die Config-ID nutzt die rohe Schreibweise aus ``provider_config.yaml``
        (z.B. ``qwen3.5-35b-a3b-q8`` mit Punkten). Nach dem Entry-Point
        ``resolve_canonical_model_id()`` wird die kanonisierte Form
        (``qwen3_5-35b-a3b-q8``) durch die Pipeline gereicht — der Lookup
        würde mit exaktem String-Match leer bleiben. Wir versuchen zuerst
        den schnellen exakten Match, danach den normalisierten Match
        (Punkt/Bindestrich → Underscore), damit beide Schreibweisen gefunden
        werden.
        """
        models = self._provider_cfg().get("models", [])
        for entry in models:
            if entry.get("id") == model_id:
                return entry
        target_normalized = self._normalize_model_name(model_id)
        if target_normalized:
            for entry in models:
                if self._normalize_model_name(entry.get("id", "")) == target_normalized:
                    return entry
        return {}

    def _resolve_model_path(self, model_id: str) -> str:
        """GGUF-Pfad aus model_file (relativ zu model_dir) auflösen."""
        cfg = self._model_cfg(model_id)
        model_file = cfg.get("model_file", "")
        if not model_file:
            raise ValueError(
                f"{self._PROVIDER_KEY}: no model_file configured for model '{model_id}'. "
                "Add a model_file entry to provider_config.yaml."
            )
        model_dir = Path(os.path.expanduser(self._model_dir()))
        return str(model_dir / model_file)

    def _resolve_model_path_from_dir(self, model_file: str, model_dir: str) -> str:
        """Pfad aus model_file (relativ zu model_dir) auflösen — ohne model_cfg Lookup."""
        resolved_dir = model_dir
        if model_dir.startswith("~"):
            resolved_dir = os.path.expanduser(model_dir)
        elif not os.path.isabs(resolved_dir):
            resolved_dir = os.path.expanduser(resolved_dir)
        return str(Path(resolved_dir) / model_file)

    def _is_remote_provider(self) -> bool:
        """True wenn der llama-server via SSH auf einer Remote-Maschine startet.

        Erkennung über server_start_cmd: beginnt der Befehl mit ``ssh``,
        läuft der Server auf einem anderen Host und ist kein lokaler
        ``Path.is_file()``-Check möglich.
        """
        return self._provider_cfg().get("server_start_cmd", "").lstrip().startswith("ssh")

    def _preflight_check_model_file(self, model_id: str) -> tuple[bool, str]:
        """Pre-Flight-Check: existiert die model_file auf der Disk?

        Verhindert 180s-Timeout, wenn der ``model_file``-Pfad in der Config
        falsch konfiguriert ist (Tippfehler, fehlende Datei, falscher
        ``model_dir``). Pitfall-Diagnose 2026-06-10: ``gemma-4-12b-it-ud-q4_k_xl``
        war mit ``...-UD-Q4_K_X.gguf`` (ohne ``L``) konfiguriert, der Server
        konnte die Datei nicht laden und lief 180s in Timeout, obwohl das
        Problem schon nach <1s erkennbar war.

        Remote-Provider (SSH): lokaler Datei-Check nicht möglich — der Pfad
        liegt auf der Remote-Maschine. Pitfall-Diagnose 2026-06-10: llamacpp_spark
        schlug immer fehl, weil ``Path.is_file()`` den Linux-Pfad auf macOS
        prüfte. Bei einem Tippfehler im Remote-Pfad bricht llama-server
        innerhalb von Sekunden mit einer klaren Fehlermeldung im Server-Log ab.

        Returns:
            (True, "") wenn die Datei existiert (oder Remote-Provider), sonst (False, fehlermeldung).
        """
        # Remote-Provider: kein lokaler Datei-Check möglich
        if self._is_remote_provider():
            return True, ""
        try:
            model_path = self._resolve_model_path(model_id)
        except ValueError as exc:
            return False, str(exc)
        if not Path(model_path).is_file():
            return False, (
                f"Model-Datei nicht gefunden für '{model_id}': '{model_path}'. "
                f"Prüfe model_file in providers.local.{self._PROVIDER_KEY}.models."
            )
        return True, ""

    # ------------------------------------------------------------------
    # Health- und Readiness-Checks
    # ------------------------------------------------------------------

    def _is_healthy(self) -> bool:
        """Returns True when the /health endpoint responds with HTTP 200."""
        try:
            with urllib.request.urlopen(self._health_url(), timeout=3) as resp:
                return resp.status == HTTP_OK
        except (urllib.error.URLError, OSError):
            return False

    def _is_model_ready(self, model_id: str) -> bool:
        """Run a tiny completion probe so benchmark starts only when model is responsive."""
        probe_timeout_sec = max(5, int(self._provider_cfg().get("server_ready_probe_timeout_sec", 10)))
        probe_url = self._chat_completions_url()
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": "Hallo"}],
            "max_tokens": 8,
            "temperature": 0.0,
        }
        req = urllib.request.Request(
            probe_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key()}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=probe_timeout_sec) as resp:
                if resp.status != HTTP_OK:
                    return False
                body = json.loads(resp.read().decode("utf-8"))
                choices = body.get("choices") or []
                if not choices:
                    return False
                choice0 = choices[0] or {}
                message = choice0.get("message") or {}
                visible_content = (message.get("content") or "").strip()
                reasoning_content = (message.get("reasoning_content") or "").strip()
                finish_reason = (choice0.get("finish_reason") or "").strip()
                usage = body.get("usage") or {}
                total_tokens = usage.get("total_tokens") or 0
                return bool(visible_content or reasoning_content or finish_reason or total_tokens > 0)
        except urllib.error.HTTPError as exc:
            self._log_probe_failure("HTTP", probe_url, probe_timeout_sec, exc, model_id)
            return False
        except urllib.error.URLError as exc:
            self._log_probe_failure("transport", probe_url, probe_timeout_sec, exc.reason, model_id)
            return False
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self._log_probe_failure("parse/runtime", probe_url, probe_timeout_sec, exc, model_id)
            return False

    def _log_probe_failure(
        self,
        kind: str,
        probe_url: str,
        timeout_sec: int,
        exc: Any,
        model_id: str,
    ) -> None:
        """Einheitliches Debug-Logging für Readiness-Probe-Fehler (DRY-1)."""
        logger.debug(
            "Readiness probe %s error (provider=%s, model=%s, url=%s, timeout=%ss): %s",
            kind, self._PROVIDER_KEY, model_id, probe_url, timeout_sec, exc,
        )

    def _query_active_model(self) -> str | None:
        """Ask the running server which model it currently serves (via /v1/models)."""
        try:
            models_url = f"{self._server_root_url()}/v1/models"
            with urllib.request.urlopen(models_url, timeout=3) as resp:
                data = json.loads(resp.read())
                entries = data.get("data", [])
                if entries:
                    return entries[0].get("id")
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        return None

    # ------------------------------------------------------------------
    # Server-Cmd-Bau
    # ------------------------------------------------------------------

    def _llama_cpp_defaults(self) -> dict[str, Any]:
        """llama_cpp_defaults-Block aus providers.local.config (DRY-3)."""
        return self._local_cfg.get("config", {}).get("llama_cpp_defaults", {})

    def _build_server_cmd(self, model_id: str) -> str:
        """Vollständigen llama-server-Befehl für die gegebene Modell-ID bauen."""
        model_path = self._resolve_model_path(model_id)
        model_cfg = self._model_cfg(model_id)
        prov_cfg = self._provider_cfg()
        llama_cpp_defaults = self._llama_cpp_defaults()

        port = _extract_port(self._base_url())

        ctx_size = model_cfg.get(
            "context_length",
            prov_cfg.get(
                "context_window",
                self._local_cfg.get("config", {}).get("context_window", 32768),
            ),
        )
        n_gpu = model_cfg.get("n_gpu_layers", prov_cfg.get("n_gpu_layers", 99))
        threads = prov_cfg.get("threads", 10)
        # Per-Modell-Override für `parallel`: ermöglicht Szenarien wie
        # Hermes 4.3 36B (Hybrid-Attention, SWA-Re-Processings) mit parallel=1
        # zu starten, während andere Modelle desselben Providers parallel=4
        # behalten. Da swap_model() pro Modellwechsel einen frischen
        # llama-server startet, ist der Per-Modell-Wert beim Server-Start
        # wirksam.
        parallel = model_cfg.get("parallel", prov_cfg.get("parallel", 4))
        log_file = os.path.expanduser(prov_cfg.get("server_log", "~/ai/llama-lab-server.log"))
        start_cmd = self._server_start_cmd()

        cmd = (
            f"{start_cmd}"
            f" -m {model_path}"
            f" --alias {model_id}"
            f" --ctx-size {ctx_size}"
            f" --n-gpu-layers {n_gpu}"
            f" --threads {threads}"
            f" --parallel {parallel}"
            f" --port {port}"
            f" --host {prov_cfg.get('bind_host', '127.0.0.1')}"
        )

        # Reproduzierbarkeits-Seed (aus Defaults, Fallback 42 statt llama.cpp-Random)
        seed = llama_cpp_defaults.get("seed", 42)
        cmd += f" --seed {seed}"

        # Sampling-Parameter: model_cfg-Override > llama_cpp_defaults > hardcoded Fallback
        # (eine einzige Schleife statt vorher zwei — siehe BUG-1 in der Analyse)
        for cfg_key, flag, hardcoded_fallback in _SAMPLING_PARAMS:
            default_value = llama_cpp_defaults.get(cfg_key, hardcoded_fallback)
            value = model_cfg.get(cfg_key, default_value)
            cmd += f" {flag} {value}"

        # Optional model-level runtime tuning
        reasoning_mode = model_cfg.get("reasoning")
        if reasoning_mode:
            cmd += f" --reasoning {reasoning_mode}"
        enable_thinking = model_cfg.get("enable_thinking")
        if enable_thinking in (True, False):
            # Server-Log empfiehlt: "Use --reasoning on / --reasoning off instead"
            # --chat-template-kwargs ist deprecated und verursacht JSON-Parse-Errors
            # bei SSH-Remote-Commands (Quotes gehen verloren).
            cmd += f" --reasoning {'on' if enable_thinking else 'off'}"

        # Draft-Modell für Speculative Decoding (z.B. MTP).
        # model_draft_file ist relativ zu model_dir; wird zum Full-Path aufgelöst.
        draft_file = model_cfg.get("model_draft_file")
        if draft_file:
            draft_path = self._resolve_model_path_from_dir(draft_file, prov_cfg.get("model_dir"))
            cmd += f" --model-draft {draft_path}"

        # Zusätzliche Server-Flags aus der Modell-Config (extra_server_args).
        # Ermöglicht die Übergabe beliebiger llama.cpp-Flags wie --spec-type,
        # --spec-draft-n-max, --flash-attn, --jinja, --cache-type-k/v etc.
        # Beispiel in provider_config.yaml:
        #   extra_server_args:
        #     - "--spec-type draft-mtp"
        #     - "--spec-draft-n-max 2"
        extra_args = model_cfg.get("extra_server_args", [])
        if isinstance(extra_args, list):
            for arg in extra_args:
                if isinstance(arg, str) and arg.strip():
                    cmd += f" {arg.strip()}"

        return f"{cmd} >> {log_file} 2>&1"

    # ------------------------------------------------------------------
    # OpenAI-Client (lazy-loaded, recreated on base_url change)
    # ------------------------------------------------------------------

    @property
    def client(self) -> Any:
        """Lazy-load the OpenAI-compat client pointing at the llama.cpp server.

        FIX: Keep-Alive deaktiviert (max_keepalive_connections=0) um Connection-Leaks
        zu verhindern. Der Remote-Server (SSH) schließt Verbindungen nach langen
        Requests, aber der httpx-Connection-Pool merkt es nicht. Der nächste Request
        hängt dann im CLOSE_WAIT-Zustand.
        """
        if OpenAI is None:
            raise ImportError(
                "Library 'openai' not installed. Run: pip install openai"
            )
        current_base_url = self._base_url()
        if self._client is not None and self._client_base_url == current_base_url:
            return self._client

        import httpx  # lokaler Import: nur aktiv, wenn openai lib vorhanden

        prov_cfg = self._provider_cfg()
        read_timeout = float(prov_cfg.get("read_timeout", 300.0))
        timeout_cfg = httpx.Timeout(connect=10.0, read=read_timeout, write=300.0, pool=300.0)
        limits = httpx.Limits(max_keepalive_connections=0, max_connections=10)
        http_client = httpx.Client(timeout=timeout_cfg, limits=limits)
        self._client = OpenAI(
            base_url=current_base_url,
            api_key=self._api_key(),
            http_client=http_client,
            max_retries=1,  # Begrenze OpenAI-Library-Retries bei Connection-Errors
        )
        self._client_base_url = current_base_url
        return self._client

    # ------------------------------------------------------------------
    # Server-Lifecycle
    # ------------------------------------------------------------------

    def is_server_running(self) -> bool:
        """Returns True when the llama.cpp /health endpoint responds with 200."""
        return self._is_healthy()

    def _wait_for_model_ready(
        self,
        model_id: str | None,
        *,
        timeout_sec: int,
        poll_sec: int,
        log_prefix: str,
    ) -> bool:
        """Polle /health + Readiness-Probe, bis Server modellbereit oder Timeout (DRY-2).

        Returns:
            True wenn Modell innerhalb des Timeouts bereit war, sonst False.
        """
        poll_sec = max(1, poll_sec)
        attempts = max(1, (timeout_sec + poll_sec - 1) // poll_sec)
        for attempt in range(attempts):
            time.sleep(poll_sec)
            if not self._is_healthy():
                logger.debug(
                    "%s health pending (provider=%s, model=%s, attempt=%d/%d)",
                    log_prefix, self._PROVIDER_KEY, model_id, attempt + 1, attempts,
                )
                continue
            if model_id and not self._is_model_ready(model_id):
                logger.debug(
                    "%s readiness probe pending (provider=%s, model=%s, attempt=%d/%d)",
                    log_prefix, self._PROVIDER_KEY, model_id, attempt + 1, attempts,
                )
                continue
            return True
        return False

    def start_server(self, model_id: str | None = None) -> bool:
        """Start the llama.cpp server for the given model id.

        Baut den vollständigen llama-server-Befehl, startet ihn im Hintergrund
        und wartet bis zu `server_ready_timeout_sec` auf /health. Falls der
        Server bereits mit einem ANDEREN Modell läuft, wird er gestoppt und
        neu gestartet (entspricht swap_model).

        Args:
            model_id: Config-ID des zu ladenden Modells.

        Returns:
            True bei erfolgreichem Start, False sonst.
        """
        healthy = self._is_healthy()

        _active_normalized = self._normalize_model_name(self._active_model)
        _model_normalized = self._normalize_model_name(model_id)
        _models_match = _active_normalized == _model_normalized

        # Pfad 1: Server läuft bereits mit dem gewünschten Modell
        if (
            healthy
            and self._active_model
            and _models_match
            and model_id
            and self._is_model_ready(model_id)
        ):
            logger.debug("llama.cpp server already running at %s", self._base_url())
            return True

        # Pfad 2: Server gesund, aber kein _active_model gesetzt → versuchen zu adoptieren
        if healthy and self._active_model is None:
            detected = self._query_active_model()
            if self._detected_matches_model(detected, model_id):
                if model_id and self._is_model_ready(model_id):
                    self._active_model = model_id
                    logger.debug(
                        "Adopting already running llama.cpp endpoint at %s with model '%s'",
                        self._base_url(), model_id,
                    )
                    return True

                prov_cfg = self._provider_cfg()
                adopt_timeout = int(prov_cfg.get(
                    "existing_server_ready_timeout_sec",
                    prov_cfg.get("server_ready_timeout_sec", 60),
                ))
                adopt_poll = int(prov_cfg.get("server_ready_poll_sec", 5))
                print(
                    f"   ⏳ Server läuft bereits mit '{model_id}' — "
                    f"warte auf Modell-Bereitschaft (Timeout: {adopt_timeout}s) ...",
                    flush=True,
                )
                if self._wait_for_model_ready(
                    model_id, timeout_sec=adopt_timeout, poll_sec=adopt_poll,
                    log_prefix="Adopt warmup",
                ):
                    self._active_model = model_id
                    print(f"   ✅ Modell bereit nach {adopt_timeout}s                              ", flush=True)
                    logger.debug(
                        "Adopted already running llama.cpp endpoint at %s with model '%s'",
                        self._base_url(), model_id,
                    )
                    return True

                warning = (
                    f"OpenAI-kompatibler Endpunkt unter {self._base_url()} läuft bereits mit '{model_id}', "
                    "antwortet aber auch nach Wartezeit noch nicht stabil auf den Hallo-Probe-Request. "
                    "Benchmark wird beendet."
                )
                logger.warning(warning)
                print(f"   ⚠️  {warning}")
                return False

            # Endpoint-Konflikt: anderes Modell läuft → Server stoppen und neu starten
            warning = (
                f"OpenAI-kompatibler Endpunkt unter {self._base_url()} ist bereits aktiv"
                f"{f' (aktives Modell: {detected})' if detected else ''}. "
                f"Starte Server mit '{model_id}' neu..."
            )
            logger.warning(warning)
            print(f"   ⚠️  {warning}")
            self.stop_server()
            time.sleep(2)
            return self.start_server(model_id)

        # Pfad 3: Server läuft mit einem ANDEREN bekannten Modell → Restart
        if healthy and self._active_model and self._active_model != model_id:
            logger.debug(
                "llama.cpp server running with managed model '%s', restarting for '%s'",
                self._active_model, model_id,
            )
            self.stop_server()
            time.sleep(2)
            return self.start_server(model_id)

        # Pfad 4: Cold-Start — llama-server launchen und auf Readiness warten
        # Pre-Flight-Check: existiert die model_file auf der Disk? Spart 180s Timeout
        # bei Tippfehlern in `model_file` (z.B. fehlendes 'L' bei Q4_K_XL).
        if model_id:
            ok, err = self._preflight_check_model_file(model_id)
            if not ok:
                logger.error(err)
                print(f"   ❌ {err}")
                return False

        cmd = self._build_server_cmd(model_id) if model_id else self._server_start_cmd()
        logger.debug("Starting llama.cpp server: %s", cmd)
        print(f"   ⏳ Starte llama.cpp Server ({model_id}) ...")
        try:
            proc = subprocess.Popen(  # pylint: disable=consider-using-with
                cmd,
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._server_pid = proc.pid
        except OSError as exc:
            logger.error("Failed to launch llama.cpp server: %s", exc)
            return False

        prov_cfg = self._provider_cfg()
        # Per-Modell-Override hat Vorrang: große Modelle (z.B. Multi-Part-Split-GGUFs)
        # brauchen länger als der Provider-Default → server_ready_timeout_sec im Modell-Eintrag setzen.
        _mcfg = self._model_cfg(model_id) if model_id else {}
        ready_timeout = int(
            _mcfg.get("server_ready_timeout_sec")
            or prov_cfg.get("server_ready_timeout_sec", 60)
        )
        ready_poll = int(prov_cfg.get("server_ready_poll_sec", 5))
        if self._wait_for_model_ready(
            model_id, timeout_sec=ready_timeout, poll_sec=ready_poll, log_prefix="llama.cpp",
        ):
            self._active_model = model_id
            print(f"   ✅ Server bereit ({ready_timeout}s)")
            logger.debug("llama.cpp server ready within %d s", ready_timeout)
            return True

        logger.error("llama.cpp server did not become ready within %d s.", ready_timeout)
        return False

    def _detected_matches_model(self, detected: str | None, model_id: str | None) -> bool:
        """Prüfe, ob das vom Server gemeldete Modell dem gewünschten entspricht."""
        if not (detected and model_id):
            return False
        detected_normalized = self._strip_model_name(detected)
        model_normalized = self._strip_model_name(model_id)
        return (
            model_normalized in detected_normalized
            or detected_normalized in model_normalized
            or detected == model_id
        )

    def stop_server(self) -> None:
        """Stop the llama.cpp server — by PID if known, then always via stop command."""
        if self._server_pid is not None:
            logger.debug("Stopping llama.cpp server (PID %d)", self._server_pid)
            try:
                subprocess.run(["kill", str(self._server_pid)], check=False)
            except OSError as exc:
                logger.warning("Could not kill PID %d: %s", self._server_pid, exc)
            self._server_pid = None

        cmd = self._server_stop_cmd()
        logger.debug("Stopping llama.cpp server via stop command: %s", cmd)
        try:
            subprocess.run(cmd, shell=True, check=False)
        except OSError as exc:
            logger.warning("Could not stop llama.cpp server: %s", exc)

        self._active_model = None
        self._client = None
        self._client_base_url = None

    def _run_cleanup(self) -> None:
        """Post-Stop-Cleanup (Cache-Bereinigung) — typischerweise für Remote-Provider."""
        post_stop_cmd = self._provider_cfg().get("server_post_stop_cmd")
        if not post_stop_cmd:
            return

        logger.debug("Running post-stop cleanup: %s", post_stop_cmd)
        try:
            subprocess.run(post_stop_cmd, shell=True, check=False)
        except OSError as exc:
            logger.warning("Post-stop cleanup failed: %s", exc)

    def swap_model(self, model_id: str) -> bool:
        """Stop current server and restart it with the new model."""
        logger.debug("Swapping llama.cpp model to: %s", model_id)
        self.stop_server()

        if self._provider_cfg().get("server_post_stop_cmd"):
            print("   🧹 Cache-Cleanup nach Modell-Wechsel...")
            self._run_cleanup()
            time.sleep(3)
        else:
            time.sleep(2)

        return self.start_server(model_id)

    # ------------------------------------------------------------------
    # BaseProviderClient interface
    # ------------------------------------------------------------------

    def is_accessible(self) -> bool:
        """Returns True when the /health endpoint is reachable."""
        return self._is_healthy()

    def _ensure_model_ready(self, model: str) -> bool:
        """Stellt sicher, dass `model` auf dem llama.cpp-Server geladen ist (DRY).

        Returns:
            True wenn Modell bereit (oder bereits geladen), sonst False.
        """
        _active_normalized = self._normalize_model_name(self._active_model)
        _model_normalized = self._normalize_model_name(model)
        _models_match = _active_normalized == _model_normalized

        # Aktives Modell stimmt → Re-Validierung gegen Server (Stale-Ready-Schutz)
        if self._active_model and _models_match:
            if self._is_healthy() and self._is_model_ready(model):
                return True
            logger.debug(
                "Stale-Ready erkannt: _active_model='%s' aber Server nicht erreichbar "
                "oder Modell nicht bereit — Neustart.",
                model,
            )
            self._active_model = None
            return self.start_server(model)

        if self._active_model is None:
            return self.start_server(model)
        return self.swap_model(model)

    def _build_messages(self, prompt: str, system_prompt: str | None) -> list[dict[str, str]]:
        """Chat-Messages-Liste mit optionalem System-Prompt bauen (DRY)."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _extract_response_content(
        self,
        response: Any,
        model: str,
    ) -> str:
        """Content + Reasoning aus OpenAI-kompatibler Response extrahieren (DRY).

        Setzt ``self.last_response_metadata`` mit allen beobachtbaren Feldern.
        """
        msg = response.choices[0].message if response.choices else None
        content = (msg.content or "") if msg else ""
        reasoning = (getattr(msg, "reasoning_content", None) or "") if msg else ""

        self.last_response_metadata.update(
            {
                "model": getattr(response, "model", model),
                "usage": getattr(response, "usage", None),
                "finish_reason": (
                    response.choices[0].finish_reason if response.choices else None
                ),
            }
        )

        if reasoning:
            usage = getattr(response, "usage", None)
            # reasoning_tokens: bevorzugt aus usage.completion_tokens_details
            # (llama.cpp >= b5XXX), sonst Fallback auf completion_tokens wenn
            # kein Content vorhanden ist.
            rt: int | None = None
            if usage:
                ctd = getattr(usage, "completion_tokens_details", None)
                if ctd:
                    rt = getattr(ctd, "reasoning_tokens", None)
                if rt is None and not content.strip():
                    rt = getattr(usage, "completion_tokens", 0)
            if rt is not None:
                self.last_response_metadata["reasoning_tokens"] = rt
            self.last_response_metadata["think_content"] = reasoning

        return content

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> str:
        """Send a chat completion request to the llama.cpp server.

        Automatisches Model-Swapping, wenn `model` vom aktiven Modell abweicht.
        """
        if not self._ensure_model_ready(model):
            raise RuntimeError(
                f"llamacpp endpoint conflict or startup failure for model '{model}'"
            )

        # FIX: Client nach langen Queries zurücksetzen, um Connection-Leaks zu verhindern.
        _should_reset = not getattr(self, "_skip_llamacpp_cleanup", False)
        if _should_reset:
            self._client = None
            self._client_base_url = None

        messages = self._build_messages(prompt, kwargs.get("system"))

        _prov_cfg = self._provider_cfg()
        token_param_name = _prov_cfg.get("token_param_name", "max_tokens")
        raw_requested: int | None = kwargs.get("max_tokens")
        initial_tokens, _ = resolve_token_budget(
            model, raw_requested, self.config, kwargs.get("_module_key")
        )
        model_cfg_max_tokens = self._model_cfg(model).get("max_tokens")
        if model_cfg_max_tokens is not None:
            initial_tokens = min(initial_tokens, model_cfg_max_tokens)

        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if stream_handler:
            params["stream"] = True

        response_or_stream, used_max_tokens, fallback_triggered = (
            self._execute_with_token_fallback(
                func=self.client.chat.completions.create,
                token_param_name=token_param_name,
                initial_max_tokens=initial_tokens,
                error_keywords=[
                    "maximum context length",
                    "max_tokens",
                    "context window",
                    "too large",
                    "context_length_exceeded",
                ],
                func_kwargs=params,
            )
        )

        self.last_response_metadata = {
            "token_limit_fallback": fallback_triggered,
            "token_limit_used": used_max_tokens,
        }

        if stream_handler:
            full_content = ""
            for chunk in response_or_stream:
                if hasattr(chunk, "usage") and chunk.usage:
                    self.last_response_metadata["usage"] = chunk.usage
                if chunk.choices:
                    finish = getattr(chunk.choices[0], "finish_reason", None)
                    if finish:
                        self.last_response_metadata["finish_reason"] = finish
                    delta = chunk.choices[0].delta.content
                    if delta:
                        stream_handler(delta)
                        full_content += delta
            return full_content

        return self._extract_response_content(response_or_stream, model)

    def get_available_models(self) -> list[str]:
        """Returns the list of models the server currently advertises via /v1/models,
        falling back to the static model list in provider_config.yaml."""
        try:
            resp = self.client.models.list()
            return [m.id for m in resp.data]
        except Exception as exc:
            logger.debug("Could not list llama.cpp models from server: %s", exc)

        return [
            m.get("id", "")
            for m in self._provider_cfg().get("models", [])
            if m.get("id")
        ]
