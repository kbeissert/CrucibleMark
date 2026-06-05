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
import shlex
import json
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

    PROVIDER_NAMES = ["llamacpp", "llama_cpp", "llamacpp_local", "llamacpp_spark"]

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self._client: Optional[Any] = None
        self._client_base_url: Optional[str] = None
        self._active_model: Optional[str] = None
        self._server_pid: Optional[int] = None
        self._provider_name: str = "llamacpp"

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_provider_name(provider_name: Optional[str]) -> str:
        """Map legacy aliases to canonical local provider keys."""
        alias_map = {
            "llama_cpp": "llamacpp",
            "llamacpp_local": "llamacpp",
        }
        if not provider_name:
            return "llamacpp"
        return alias_map.get(provider_name, provider_name)

    def _set_provider_context(self, provider_name: Optional[str]) -> None:
        """Set active provider context for config lookup (llamacpp or llamacpp_spark)."""
        normalized = self._normalize_provider_name(provider_name)
        if normalized != self._provider_name:
            self._provider_name = normalized
            self._client = None
            self._client_base_url = None
            self._active_model = None
            logger.debug("Switched llama.cpp provider context to '%s'", normalized)
            return
        self._provider_name = normalized

    def _provider_cfg(self) -> Dict[str, Any]:
        local_cfg = self.config.get("providers", {}).get("local", {})
        provider_cfg = local_cfg.get(self._provider_name, {})
        if provider_cfg:
            return provider_cfg
        return local_cfg.get("llamacpp", {})

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

    def _chat_completions_url(self) -> str:
        return f"{self._server_root_url()}/v1/chat/completions"

    def _is_healthy(self) -> bool:
        """Returns True when the /health endpoint responds with HTTP 200."""
        try:
            with urllib.request.urlopen(self._health_url(), timeout=3) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError):
            return False

    def _is_model_ready(self, model_id: str) -> bool:
        """Run a tiny completion probe so benchmark starts only when model is responsive."""
        probe_timeout_sec = int(self._provider_cfg().get("server_ready_probe_timeout_sec", 10))
        probe_timeout_sec = max(5, probe_timeout_sec)
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
                if resp.status != 200:
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
            logger.debug(
                "Readiness probe HTTP error (provider=%s, model=%s, url=%s, timeout=%ss): %s",
                self._provider_name,
                model_id,
                probe_url,
                probe_timeout_sec,
                exc,
            )
            return False
        except urllib.error.URLError as exc:
            logger.debug(
                "Readiness probe transport error (provider=%s, model=%s, url=%s, timeout=%ss): %s",
                self._provider_name,
                model_id,
                probe_url,
                probe_timeout_sec,
                exc.reason,
            )
            return False
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            logger.debug(
                "Readiness probe parse/runtime error (provider=%s, model=%s, url=%s, timeout=%ss): %s",
                self._provider_name,
                model_id,
                probe_url,
                probe_timeout_sec,
                exc,
            )
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
            f" --host {prov_cfg.get('bind_host', '127.0.0.1')}"
        )

        # Optional model-level runtime tuning (reasoning/profile-specific).
        # These flags are only appended when explicitly set in provider_config.yaml.
        if model_cfg.get("reasoning"):
            cmd += f" --reasoning {model_cfg['reasoning']}"

        enable_thinking = model_cfg.get("enable_thinking")
        if enable_thinking in (True, False):
            kwargs_json = json.dumps({"enable_thinking": bool(enable_thinking)})
            cmd += f" --chat-template-kwargs {shlex.quote(kwargs_json)}"

        optional_numeric_flags = {
            "temperature": "--temp",
            "top_p": "--top-p",
            "top_k": "--top-k",
            "min_p": "--min-p",
            "presence_penalty": "--presence-penalty",
            "repeat_penalty": "--repeat-penalty",
        }
        for cfg_key, flag in optional_numeric_flags.items():
            if model_cfg.get(cfg_key) is not None:
                cmd += f" {flag} {model_cfg[cfg_key]}"

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
        current_base_url = self._base_url()
        if self._client is None or self._client_base_url != current_base_url:
            import httpx

            timeout_cfg = httpx.Timeout(connect=10.0, read=300.0, write=300.0, pool=300.0)
            self._client = OpenAI(
                base_url=current_base_url,
                api_key=self._api_key(),
                timeout=timeout_cfg,
            )
            self._client_base_url = current_base_url
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
        healthy = self._is_healthy()

        if healthy and self._active_model == model_id:
            if model_id and self._is_model_ready(model_id):
                logger.debug("llama.cpp server already running at %s", self._base_url())
                return True

        if healthy and self._active_model is None:
            detected = self._query_active_model()
            if detected == model_id and model_id and self._is_model_ready(model_id):
                self._active_model = model_id
                logger.debug(
                    "Adopting already running llama.cpp endpoint at %s with model '%s'",
                    self._base_url(),
                    model_id,
                )
                return True

            if detected == model_id:
                adopt_ready_timeout_sec = int(
                    self._provider_cfg().get(
                        "existing_server_ready_timeout_sec",
                        self._provider_cfg().get("server_ready_timeout_sec", 60),
                    )
                )
                adopt_poll_sec = int(self._provider_cfg().get("server_ready_poll_sec", 5))
                adopt_poll_sec = max(1, adopt_poll_sec)
                adopt_attempts = max(
                    1,
                    (adopt_ready_timeout_sec + adopt_poll_sec - 1) // adopt_poll_sec,
                )
                for attempt in range(adopt_attempts):
                    if self._is_model_ready(model_id):
                        self._active_model = model_id
                        logger.debug(
                            "Adopted already running llama.cpp endpoint at %s with model '%s' after warmup (%d/%d)",
                            self._base_url(),
                            model_id,
                            attempt + 1,
                            adopt_attempts,
                        )
                        return True
                    if attempt + 1 < adopt_attempts:
                        time.sleep(adopt_poll_sec)

                warning = (
                    f"OpenAI-kompatibler Endpunkt unter {self._base_url()} läuft bereits mit '{model_id}', "
                    "antwortet aber auch nach Wartezeit noch nicht stabil auf den Hallo-Probe-Request. "
                    "Benchmark wird beendet."
                )
            else:
                warning = (
                    f"OpenAI-kompatibler Endpunkt unter {self._base_url()} ist bereits aktiv"
                    f"{f' (aktives Modell: {detected})' if detected else ''}. "
                    f"Benchmark für '{model_id}' wird nicht gestartet, um den laufenden Server nicht zu überschreiben."
                )
            logger.warning(warning)
            print(f"   ⚠️  {warning}")
            return False

        if healthy and self._active_model and self._active_model != model_id:
            logger.debug(
                "llama.cpp server running with managed model '%s', restarting for '%s'",
                self._active_model,
                model_id,
            )
            self.stop_server()
            time.sleep(2)

        cmd = self._build_server_cmd(model_id) if model_id else self._server_start_cmd()
        logger.debug("Starting llama.cpp server: %s", cmd)
        print(f"   ⏳ Starte llama.cpp Server ({model_id}) ...")
        try:
            # stdin/stdout/stderr explizit auf DEVNULL setzen, damit der bash-Wrapper-
            # Prozess keine offenen File-Descriptors (z.B. PIPE write-ends) erbt.
            # Der Server selbst loggt via Shell-Redirect (>> server.log 2>&1).
            # Popen wird bewusst NICHT als Context Manager verwendet: der Prozess läuft
            # im Hintergrund weiter — ein `with`-Block würde ihn beim Verlassen beenden.
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

        # Wait until ready (provider-configurable timeout for slower remote loads).
        ready_timeout_sec = int(self._provider_cfg().get("server_ready_timeout_sec", 60))
        poll_interval_sec = int(self._provider_cfg().get("server_ready_poll_sec", 5))
        poll_interval_sec = max(1, poll_interval_sec)
        attempts = max(1, (ready_timeout_sec + poll_interval_sec - 1) // poll_interval_sec)
        for attempt in range(attempts):
            time.sleep(poll_interval_sec)
            if not self._is_healthy():
                logger.debug(
                    "llama.cpp health pending (provider=%s, model=%s, attempt=%d/%d)",
                    self._provider_name,
                    model_id,
                    attempt + 1,
                    attempts,
                )
                continue
            if model_id and not self._is_model_ready(model_id):
                logger.debug(
                    "llama.cpp readiness probe pending (provider=%s, model=%s, attempt=%d/%d)",
                    self._provider_name,
                    model_id,
                    attempt + 1,
                    attempts,
                )
                continue
            elapsed = (attempt + 1) * poll_interval_sec
            logger.debug("llama.cpp server ready after ~%ds", elapsed)
            print(f"   ✅ Server bereit ({elapsed}s)")
            self._active_model = model_id
            return True

        logger.error("llama.cpp server did not become ready within %d s.", ready_timeout_sec)
        return False

    def stop_server(self) -> None:
        """Stop the llama.cpp server — by PID if known, then always via stop command.

        Der PID-Kill beendet nur den lokalen Prozess (z.B. SSH-Wrapper bei Remote-Providern).
        Der Fallback-Stop via server_stop_cmd wird immer ausgeführt, um sicherzustellen,
        dass auch Remote-Server (DGX Spark via SSH) zuverlässig gestoppt werden.
        """
        if self._server_pid is not None:
            logger.debug("Stopping llama.cpp server (PID %d)", self._server_pid)
            try:
                subprocess.run(["kill", str(self._server_pid)], check=False)
            except OSError as exc:
                logger.warning("Could not kill PID %d: %s", self._server_pid, exc)
            self._server_pid = None

        # Fallback-Stop immer ausführen — PID-Kill reicht bei SSH-Wrappern nicht aus,
        # da nur der lokale SSH-Prozess beendet wird, nicht der Remote-Server.
        cmd = self._server_stop_cmd()
        logger.debug("Stopping llama.cpp server via stop command: %s", cmd)
        try:
            subprocess.run(cmd, shell=True, check=False)
        except OSError as exc:
            logger.warning("Could not stop llama.cpp server: %s", exc)

        self._active_model = None
        self._client = None
        self._client_base_url = None

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
        self._set_provider_context(kwargs.pop("_provider_name", None))

        # Start only when needed. If a foreign endpoint is active on the same base_url,
        # start_server() warns and returns False without stopping that process.
        if self._active_model == model:
            # Health-Check vor Stale-Ready: Server könnte zwischenzeitlich gestoppt worden sein
            # (z.B. durch _cleanup_local_provider nach einem vorherigen Modul-Run).
            if self._is_healthy():
                ready = True
            else:
                logger.debug(
                    "Stale-Ready erkannt: _active_model='%s' aber Server nicht erreichbar — Neustart.",
                    model,
                )
                self._active_model = None
                ready = self.start_server(model)
        elif self._active_model is None:
            ready = self.start_server(model)
        else:
            ready = self.swap_model(model)

        if not ready:
            raise RuntimeError(
                f"llamacpp endpoint conflict or startup failure for model '{model}'"
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
