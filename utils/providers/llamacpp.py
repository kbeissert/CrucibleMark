"""
llama.cpp Provider Client — OpenAI-compatible local inference server.

Jedes Modell wird explizit in benchmark_config.yaml unter
`providers.local.llamacpp.models` eingetragen:

  - id:            API-Bezeichner (wird an /v1/chat/completions als `model` übergeben)
  - model_file:    GGUF-Dateiname relativ zu `model_dir`
  - context_length: optionales Überschreiben des globalen Kontextfensters
  - n_gpu_layers:  GPU-Offload-Schichten (0 = reiner CPU-Betrieb)

Der Client baut daraus automatisch den vollständigen `llama-server`-Befehl
(inkl. --alias, --ctx-size, --n-gpu-layers) und swappt das Modell beim Wechsel.
"""
import logging
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from utils.providers.base import BaseProviderClient

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


class LlamaCppClient(BaseProviderClient):
    """Provider client for a local llama.cpp server (OpenAI-compatible API)."""

    PROVIDER_NAMES = ["llamacpp", "llama_cpp", "llamacpp_local"]

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self._client: Optional[Any] = None
        self._active_model: Optional[str] = None
        self._server_pid: Optional[int] = None

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------

    def _provider_cfg(self) -> Dict[str, Any]:
        return (
            self.config.get("providers", {})
            .get("local", {})
            .get("llamacpp", {})
        )

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
        """Base URL without the /v1 suffix, e.g. http://127.0.0.1:1235."""
        return self._base_url().rstrip("/").removesuffix("/v1")

    def _health_url(self) -> str:
        return f"{self._server_root_url()}/health"

    def _is_healthy(self) -> bool:
        """Returns True when the /health endpoint responds with HTTP 200."""
        try:
            with urllib.request.urlopen(self._health_url(), timeout=3) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError):
            return False

    def _query_active_model(self) -> Optional[str]:
        """Ask the running server which model it currently serves (via /v1/models).

        Returns the first model id reported by the API, or None on failure.
        This lets a fresh client instance detect an already-loaded model
        without relying on the in-process _active_model state.
        """
        try:
            models_url = f"{self._server_root_url()}/v1/models"
            with urllib.request.urlopen(models_url, timeout=3) as resp:
                import json as _json
                data = _json.loads(resp.read())
                entries = data.get("data", [])
                if entries:
                    return entries[0].get("id")
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        return None

    def _model_cfg(self, model_id: str) -> Dict[str, Any]:
        """Return the config dict for a model id, or empty dict if not found."""
        for entry in self._provider_cfg().get("models", []):
            if entry.get("id") == model_id:
                return entry
        return {}

    def _resolve_model_path(self, model_id: str) -> str:
        """
        Resolve the full GGUF path for a model id.

        Reads model_file from the model's config entry and joins it with model_dir.
        Raises ValueError when model_file is missing.
        """
        cfg = self._model_cfg(model_id)
        model_file = cfg.get("model_file", "")
        if not model_file:
            raise ValueError(
                f"llamacpp: no model_file configured for model '{model_id}'. "
                "Add a model_file entry to benchmark_config.yaml."
            )
        model_dir = Path(os.path.expanduser(self._model_dir()))
        return str(model_dir / model_file)

    def _build_server_cmd(self, model_id: str) -> str:
        """
        Build the full llama-server command for a given model id.

        Includes --alias (so the API accepts the config id as model name),
        --ctx-size and --n-gpu-layers when set in the model config.
        Port and host are derived from base_url.
        """
        model_path = self._resolve_model_path(model_id)
        model_cfg = self._model_cfg(model_id)
        prov_cfg = self._provider_cfg()

        # Parse port from base_url (e.g. "http://127.0.0.1:1235/v1" → 1235)
        base_url = self._base_url()
        port = 1235
        try:
            port = int(base_url.split(":")[2].split("/")[0])
        except (IndexError, ValueError):
            pass

        ctx_size = model_cfg.get(
            "context_length",
            self.config.get("providers", {}).get("local", {}).get("config", {}).get("context_window", 32768),
        )
        n_gpu = model_cfg.get("n_gpu_layers", prov_cfg.get("n_gpu_layers", 99))
        threads = prov_cfg.get("threads", 10)
        parallel = prov_cfg.get("parallel", 4)
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
            f" --host 127.0.0.1"
        )
        # Redirect server output to log file (matches llama-lab-select.sh behavior)
        return f"{cmd} >> {log_file} 2>&1"

    # ------------------------------------------------------------------
    # OpenAI client (lazy-loaded, recreated on base_url change)
    # ------------------------------------------------------------------

    @property
    def client(self) -> Any:
        """Lazy-load the OpenAI-compat client pointing at the llama.cpp server."""
        if OpenAI is None:
            raise ImportError(
                "Library 'openai' not installed. Run: pip install openai"
            )
        if self._client is None:
            import httpx

            timeout_cfg = httpx.Timeout(connect=10.0, read=300.0, write=300.0, pool=300.0)
            self._client = OpenAI(
                base_url=self._base_url(),
                api_key=self._api_key(),
                timeout=timeout_cfg,
            )
        return self._client

    # ------------------------------------------------------------------
    # Server lifecycle
    # ------------------------------------------------------------------

    def is_server_running(self) -> bool:
        """Returns True when the llama.cpp /health endpoint responds with 200."""
        return self._is_healthy()

    def start_server(self, model_id: Optional[str] = None) -> bool:
        """
        Start the llama.cpp server for the given model id.

        Builds the full llama-server command from the model's config entry
        (model_file, context_length, n_gpu_layers, threads, parallel),
        launches it in the background and waits up to 60 s for /health.

        If the server is already running with a DIFFERENT model, it is stopped
        first (equivalent to swap_model).

        Args:
            model_id: Config id of the model to load.

        Returns:
            True when the server is healthy, False otherwise.
        """
        if self._is_healthy() and self._active_model == model_id:
            logger.debug("llama.cpp server already running at %s", self._base_url())
            return True

        # _active_model unbekannt (z.B. Sub-Prozess): API befragen
        if self._is_healthy() and self._active_model is None:
            detected = self._query_active_model()
            if detected == model_id:
                logger.debug("llama.cpp server already running with '%s' (via API)", model_id)
                self._active_model = model_id
                return True
            elif detected:
                # Anderes Modell läuft → stoppen
                logger.debug("llama.cpp server running with '%s' (via API), need '%s' → stopping",
                             detected, model_id)
                self.stop_server()
                time.sleep(2)

        # Server läuft noch (anderes Modell bekannt) → erst stoppen
        elif self._is_healthy() and self._active_model != model_id:
            logger.debug("llama.cpp server running with '%s', stopping before loading '%s'",
                        self._active_model, model_id)
            self.stop_server()
            time.sleep(2)

        cmd = self._build_server_cmd(model_id) if model_id else self._server_start_cmd()
        logger.debug("Starting llama.cpp server: %s", cmd)
        print(f"   ⏳ Starte llama.cpp Server ({model_id}) ...")
        try:
            proc = subprocess.Popen(cmd, shell=True)
            self._server_pid = proc.pid
        except OSError as exc:
            logger.error("Failed to launch llama.cpp server: %s", exc)
            return False

        # Wait up to 60 s — poll /health (matches llama-lab-select.sh wait loop)
        for attempt in range(12):
            time.sleep(5)
            if self._is_healthy():
                logger.debug("llama.cpp server ready after ~%ds", (attempt + 1) * 5)
                print(f"   ✅ Server bereit ({(attempt + 1) * 5}s)")
                self._active_model = model_id
                return True

        logger.error("llama.cpp server did not become ready within 60 s.")
        return False

    def stop_server(self) -> None:
        """Stop the llama.cpp server — by PID if known, otherwise via stop command."""
        if self._server_pid is not None:
            logger.debug("Stopping llama.cpp server (PID %d)", self._server_pid)
            try:
                subprocess.run(["kill", str(self._server_pid)], check=False)
            except OSError as exc:
                logger.warning("Could not kill PID %d: %s", self._server_pid, exc)
            self._server_pid = None
        else:
            cmd = self._server_stop_cmd()
            logger.debug("Stopping llama.cpp server: %s", cmd)
            try:
                subprocess.run(cmd, shell=True, check=False)
            except OSError as exc:
                logger.warning("Could not stop llama.cpp server: %s", exc)
        self._active_model = None
        self._client = None

    def swap_model(self, model_id: str) -> bool:
        """
        Stop the current server and restart it with the new model.
        Returns True on success.
        """
        logger.debug("Swapping llama.cpp model to: %s", model_id)
        self.stop_server()
        time.sleep(2)
        return self.start_server(model_id)

    # ------------------------------------------------------------------
    # BaseProviderClient interface
    # ------------------------------------------------------------------

    def is_accessible(self) -> bool:
        """Returns True when the /health endpoint is reachable."""
        return self._is_healthy()

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> str:
        """Send a chat completion request to the llama.cpp server.

        Automatically swaps the server model when `model` differs from the
        currently active model.
        """
        # Auto-swap when model changes between benchmark runs
        if self._active_model != model:
            if not self.swap_model(model):
                raise RuntimeError(
                    f"llamacpp: could not start server for model '{model}'"
                )
        system_prompt: Optional[str] = kwargs.get("system")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        from utils.model_utils import resolve_token_budget

        _prov_cfg = self._provider_cfg()
        token_param_name = _prov_cfg.get("token_param_name", "max_tokens")
        raw_requested: Optional[int] = kwargs.get("max_tokens")
        initial_tokens, _ = resolve_token_budget(
            model, raw_requested, self.config, kwargs.get("_module_key")
        )

        params: Dict[str, Any] = {
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

        response = response_or_stream
        msg = response.choices[0].message if response.choices else None
        content = (msg.content or "") if msg else ""

        # Gemma-4 native thinking: separate reasoning_content field in message
        # (llama.cpp exposes this as msg.reasoning_content / msg.model_extra)
        reasoning = getattr(msg, "reasoning_content", None) or "" if msg else ""

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
            # Signal B: reasoning_tokens > 0 — enables ThinkingProbe detection
            # When content is empty, all completion_tokens were used for reasoning
            usage = getattr(response, "usage", None)
            comp_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
            if not content.strip():
                self.last_response_metadata["reasoning_tokens"] = comp_tokens
            self.last_response_metadata["thinking_content"] = reasoning

        return content

    def get_available_models(self) -> List[str]:
        """
        Returns the list of models the server currently advertises via /v1/models,
        falling back to the static model list in benchmark_config.yaml.
        """
        try:
            resp = self.client.models.list()
            return [m.id for m in resp.data]
        except Exception as exc:
            logger.debug("Could not list llama.cpp models from server: %s", exc)

        # Static fallback from config
        return [
            m.get("id", "")
            for m in self._provider_cfg().get("models", [])
            if m.get("id")
        ]
