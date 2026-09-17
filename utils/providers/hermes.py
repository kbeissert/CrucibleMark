"""
Hermes-Agent-Gateway-Connector (Agentic Track für CrucibleMark).

Der Connector nutzt den OpenAI-kompatiblen Hermes-Gateway
(``base_url``, Profil „CrucibleMark") wie eine API. Messobjekt ist
**Modell + Hermes-Loop + Werkzeuge** (Harness-Lift = Delta zum Raw-Run
desselben Modells auf derselben Backend-Hardware).

Mechanismus (Phase-0-Spike 2026-09-16, empirisch verifiziert):

- **Modellwechsel pro Request (H1):** Der Request-Body trägt
  ``model`` (Hermes-Modellname, Mapping-Feld ``hermes_model``) und
  ``provider`` (Gateway-Provider-ID, z. B. ``gx10-vllm``). Ein
  explizites ``provider``-Field wird vom Gateway immer honoriert
  (``_request_agent_overrides``); ein bloßes ``model`` würde ignoriert
  (``direct_model_requests``-Opt-in ist im CrucibleMark-Profil nicht
  gesetzt). Admin-Route (H2) und Profil-Restart (H3) entfallen.
- **Echo-Guard:** weicht das Response-``model`` vom gemappten Zielmodell ab, wirft
  der Connector (Miss-Labeling-Schutz bei ``direct_model_requests: true``).
- **Session-Isolation (D7):** Jeder Request erhält eine frische
  ``X-Hermes-Session-Id`` (UUID4). Der Gateway lädt Session-History
  aus seiner SessionDB — für eine frische ID ist diese leer, damit
  ist die Session isoliert (kein Prompt-Fingerprint-Mapping).
- **Usage:** Der Gateway aggregiert Tokens über den gesamten
  Tool-Loop (empirisch: Tool-Task ≈ 2× Single-Call-Baseline).
- **Sampling:** ``temperature``/``top_p``/``max_tokens`` im Body
  werden vom Gateway ignoriert — Sampling-Parität ist Hermes-seitig
  im Profil-Config sicherzustellen (Runbook-Schritt vor dem Lauf).
  Ausnahme Reasoning: ``model_options.reasoning.effort`` wird gemappt
  und überschreibt den Profil-Default — Parität pro Request via
  Modelleintrag ``reasoning_effort`` (config-getrieben).
- **Fail-Fast-Signatur:** Provider-/Auth-Fehler kommen als HTTP 200
  mit Fehler-Text als ``content`` und ``usage`` komplett 0 zurück —
  der Connector erkennt das an ``usage.total_tokens == 0``.

Lifecycle (D2 — Assume-Running): Der Gateway-Prozess wird nicht
verwaltet; ``is_accessible()`` prüft ``/health`` + Probe-Completion.

Elternklasse: ``BaseProviderClient`` (Auto-Registry via ``PROVIDER_NAMES``).
"""
import logging
import uuid
from collections.abc import Callable
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from utils.providers.base import BaseProviderClient

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

HTTP_OK: int = 200
DEFAULT_HERMES_TIMEOUT_SEC: float = 2400.0
DEFAULT_HERMES_PROVIDER: str = "gx10-vllm"
PROBE_TIMEOUT_SEC: int = 30
HEALTH_TIMEOUT_SEC: int = 10
SESSION_HEADER: str = "X-Hermes-Session-Id"


class HermesClient(BaseProviderClient):
    """Provider-Client für den Hermes-Agent-Gateway (CrucibleMark-Profil).

    Konfig-Key: ``providers.commercial.hermes`` in ``provider_config.yaml``.
    Bindet sich über ``PROVIDER_NAMES`` ins Auto-Registry
    (``BaseProviderClient._registry["hermes"]``).
    """

    PROVIDER_NAMES = ["hermes"]
    PROVIDER_CONFIG_KEY = "hermes"
    DEFAULT_TOKEN_PARAM = "max_tokens"

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client: Any | None = None
        # Zuletzt erzeugte Gateway-Session (D7) — für den Rückjoin auf die
        # Hermes-State-DB, wo reasoning-Felder UND reasoning-Tokens pro Session
        # persistiert werden, die der Response-Kanal nicht exportiert.
        self.hermes_session_id: str | None = None

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------

    def _api_key(self) -> str:
        """API-Key aus der Provider-Config (``${VAR}``-Auflösung). Fail-Fast."""
        raw = self._get_provider_cfg().get("api_key", "")
        resolved = self._resolve_env_ref(raw, default="")
        if not resolved:
            raise ValueError(
                "hermes: api_key nicht konfiguriert oder ${VAR} nicht auflösbar — "
                "API_SERVER_KEY in .env setzen."
            )
        return resolved

    def _base_url(self) -> str:
        return self._get_provider_cfg().get("base_url", "http://localhost:8642/v1")

    def _root_url(self) -> str:
        """Base URL ohne ``/v1``-Suffix (für ``/health``)."""
        return self._base_url().rstrip("/").removesuffix("/v1")

    def _gateway_provider(self) -> str:
        """Gateway-Provider-ID für das ``provider``-Body-Field (H1-Mechanismus)."""
        return str(self._get_provider_cfg().get("hermes_provider", DEFAULT_HERMES_PROVIDER))

    def _model_entry(self, model: str) -> dict[str, Any]:
        """Modelleintrag aus der Provider-Config — Fail-Fast bei fehlendem Mapping."""
        from utils.model_id_base import find_model_in_provider_cfg

        entry = find_model_in_provider_cfg(self._get_provider_cfg(), model)
        if not entry or not entry.get("hermes_model"):
            raise ValueError(
                f"hermes: Modelleintrag '{model}' fehlt oder hat kein "
                "'hermes_model'-Mapping — kein Silent-Fallback."
            )
        return entry

    def _map_hermes_model(self, model: str) -> str:
        """CrucibleMark-ID → Hermes-Modellname via ``hermes_model``-Feld. Fail-Fast."""
        return str(self._model_entry(model)["hermes_model"])

    def _model_payload(self, model: str) -> dict[str, Any]:
        """H1-Body-Fields: ``model`` (Hermes-Name) + ``provider`` (Gateway-ID).

        ``provider`` und ``model_options`` laufen über ``extra_body`` — der
        OpenAI-SDK lehnt unbekannte kwargs in ``create()`` strikt ab und
        merged ``extra_body`` top-level in den JSON-Body (gleiches Muster wie
        vLLM-Extensions in ``vllm_base``). Der Gateway liest beide als
        Top-Level-Body-Felder.

        ``model_options.reasoning`` bei gesetztem ``reasoning_effort`` im
        Modelleintrag: Der Gateway ignoriert Standard-Sampling im Body
        (Phase-0, Frage 4), mappt aber ``model_options.reasoning.effort`` auf
        den ``reasoning_config`` des Agent-Runs — mit Vorrang vor dem
        Profil-Default (api_server.py:2151ff.). Achtung: Für Custom-Provider
        (gx10-vllm) hängt der letzte Schritt (Agent → Server-Request) am
        ``supports_reasoning``-Gate (reasoning_params.py:68, dort False) —
        die Server-seitige Parität (Sampling + reasoning_effort medium)
        wirkt über das statische extra_body-Pinning im Hermes-Profil.
        Dieses Feld steuert Agent-Level-Reasoning und wird effektiv, sobald
        Hermes das Gate für Custom-Provider öffnet.
        """
        payload: dict[str, Any] = {"model": self._map_hermes_model(model)}
        extra: dict[str, Any] = {"provider": self._gateway_provider()}
        effort = self._model_entry(model).get("reasoning_effort")
        if effort:
            extra["model_options"] = {"reasoning": {"enabled": True, "effort": str(effort)}}
        payload["extra_body"] = extra
        return payload

    def _probe_model_id(self) -> str | None:
        """Modell-ID für den is_accessible-Probe: erstes konfiguriertes Modell."""
        models = self._get_provider_cfg().get("models") or []
        for entry in models:
            if isinstance(entry, dict) and entry.get("id"):
                return str(entry["id"])
        return None

    # ------------------------------------------------------------------
    # OpenAI-Client (lazy)
    # ------------------------------------------------------------------

    @property
    def client(self) -> Any:
        """Lazy-loaded OpenAI-SDK-Client gegen den Hermes-Gateway."""
        if OpenAI is None:
            raise ImportError("Library 'openai' not installed.")
        if self._client is None:
            import httpx

            read_timeout = float(
                self._get_provider_cfg().get("request_timeout", DEFAULT_HERMES_TIMEOUT_SEC)
            )
            timeout_cfg = httpx.Timeout(connect=10.0, read=read_timeout, write=300.0, pool=300.0)
            # max_keepalive_connections=0: kein Connection-Pooling — gepoolte
            # Verbindungen wären bei der langen Read-Wand (Agent-Loop) stale.
            limits = httpx.Limits(max_keepalive_connections=0, max_connections=10)
            http_client = httpx.Client(timeout=timeout_cfg, limits=limits)
            self._client = OpenAI(
                base_url=self._base_url(),
                api_key=self._api_key(),
                http_client=http_client,
                max_retries=0,
            )
        return self._client

    def close(self) -> None:
        """HTTP-Client schließen (TCP-FIN-Regel) — atexit-Kette greift via LLMClient."""
        client, self._client = self._client, None
        if client is not None:
            try:
                client.close()
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.debug("Schließen des Hermes-HTTP-Clients fehlgeschlagen: %s", exc)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Callable[[str], None] | None = None,
        **kwargs,
    ) -> str:
        """Query den Hermes-Gateway (Chat-Completions mit frischer Session pro Request).

        ``temperature`` wird bewusst NICHT in den Body geschrieben — der
        Gateway ignoriert Body-Sampling (Modul-Docstring, Abschnitt
        „Sampling"); die Parität liegt Hermes-seitig im Profil-Config.
        """
        params = self._build_chat_params(model, prompt, kwargs.get("system"))
        token_param_name, initial_tokens = self._resolve_request_tokens(model, kwargs)

        if stream_handler:
            params["stream"] = True
            params["stream_options"] = {"include_usage": True}

        response_or_stream, used_max_tokens, fallback_triggered = (
            self._execute_with_token_fallback(
                func=self.client.chat.completions.create,
                token_param_name=token_param_name,
                initial_max_tokens=initial_tokens,
                error_keywords=["maximum context length", "context window", "too large"],
                func_kwargs=params,
            )
        )
        if stream_handler:
            return self._process_stream(
                model, response_or_stream, stream_handler, fallback_triggered, used_max_tokens
            )
        return self._process_blocking(
            model, response_or_stream, fallback_triggered, used_max_tokens
        )

    def _build_chat_params(
        self, model: str, prompt: str, system: str | None,
    ) -> dict[str, Any]:
        """Request-Body: H1-Modell-Fields + Messages + frische Session (D7).

        System-Prompt wird als separate System-Message übergeben — der Gateway
        legt sie als ephemere Schicht ÜBER den Profil-Core (Gateway-Leistung,
        Phase-0 verifiziert).
        """
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        session_id = str(uuid.uuid4())
        self.hermes_session_id = session_id
        return {
            **self._model_payload(model),
            "messages": messages,
            "extra_headers": {SESSION_HEADER: session_id},
        }

    def _process_blocking(
        self, model: str, response: Any, fallback_triggered: bool, used_max_tokens: int,
    ) -> str:
        """Blocking-Response verarbeiten (inkl. Echo-Guard + Fail-Fast-Signatur)."""
        self._assert_hermes_echo(model, getattr(response, "model", None))
        msg = response.choices[0].message if response.choices else None
        content = (msg.content or "") if msg else ""
        reasoning = self._extract_think_from_message(msg)
        usage = response.usage
        finish_reason = getattr(response.choices[0], "finish_reason", None) if response.choices else None
        self._raise_on_hermes_failure(content, usage)
        self.last_response_metadata = {
            "model": getattr(response, "model", None),
            "id": getattr(response, "id", None),
            "usage": usage,
            "finish_reason": finish_reason,
            "token_limit_fallback": fallback_triggered,
            "token_limit_used": used_max_tokens,
            "reasoning_tokens": self._extract_reasoning_tokens(usage) if usage else None,
            "hermes_session_id": self.hermes_session_id,
        }
        if reasoning:
            self.last_response_metadata["think_content"] = reasoning
        self._record_hermes_extras(response)
        return content

    def _process_stream(
        self, model: str, response_stream: Any, stream_handler: Callable[[str], None],
        fallback_triggered: bool, used_max_tokens: int,
    ) -> str:
        """Streaming-Response verarbeiten (usage im Final-Chunk, analog openai._process_stream)."""
        from utils.providers.base import ThinkAccumulator

        full_content = ""
        think = ThinkAccumulator()
        stream_usage = None
        self.last_response_metadata = {
            "token_limit_fallback": fallback_triggered,
            "token_limit_used": used_max_tokens,
            "hermes_session_id": self.hermes_session_id,
        }
        for chunk in response_stream:
            stream_usage = self._capture_chunk_metadata(chunk, stream_usage)
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if getattr(delta, "content", None):
                stream_handler(delta.content)
                full_content += delta.content
            reasoning_piece = getattr(delta, "reasoning", None) or getattr(
                delta, "reasoning_content", None
            )
            if reasoning_piece:
                think.add(reasoning_piece)
        self._assert_hermes_echo(model, self.last_response_metadata.get("model"))
        if stream_usage is not None:
            self.last_response_metadata["usage"] = stream_usage
            self._raise_on_hermes_failure(full_content, stream_usage)
            rt = self._extract_reasoning_tokens(stream_usage)
            if rt is not None:
                self.last_response_metadata["reasoning_tokens"] = rt
        if think.has_content:
            self.last_response_metadata["think_content"] = think.content
        if self.last_response_metadata.get("hermes_completed") is False:
            logger.warning("hermes: Run nicht komplett abgeschlossen (hermes.extras prüfen).")
        return full_content

    def _capture_chunk_metadata(self, chunk: Any, stream_usage: Any) -> Any:
        """id/model/usage/finish_reason + Hermes-Extras aus einem SSE-Chunk in die Metadata.

        ``hermes``/``completed`` werden auch hier gelesen (nicht nur im
        Blocking-Pfad über ``_record_hermes_extras``), weil Benchmarks gegen
        den Gateway default über den Streaming-Pfad laufen (llm_client hängt
        den Default-Stream-Printer an).
        """
        if not self.last_response_metadata.get("id") and getattr(chunk, "id", None):
            self.last_response_metadata["id"] = chunk.id
        if not self.last_response_metadata.get("model") and getattr(chunk, "model", None):
            self.last_response_metadata["model"] = chunk.model
        if getattr(chunk, "usage", None):
            stream_usage = chunk.usage
        if chunk.choices and getattr(chunk.choices[0], "finish_reason", None):
            self.last_response_metadata["finish_reason"] = chunk.choices[0].finish_reason
        if getattr(chunk, "hermes", None):
            self.last_response_metadata["hermes_extras"] = chunk.hermes
        if getattr(chunk, "completed", None) is False:
            self.last_response_metadata["hermes_completed"] = False
        return stream_usage

    def _assert_hermes_echo(self, model: str, echoed: Any) -> None:
        """Echo-Guard: Antwort-``model`` muss dem gemappten Zielmodell entsprechen.

        Hintergrund (Memory-Probe 2026-09-16): ``direct_model_requests: true``
        validiert das Body-``model`` am Backend — ein abweichendes Echo bedeutet,
        dass ein anderes Modell geantwortet hat als der Benchmark-Record behauptet
        (Miss-Labeling). Das ist der stille Fehlerfall, den die Flag-Variante
        verhindert; dieser Guard macht ihn laut. Fehlendes/leeres Echo ist nicht
        prüfbar und wird toleriert (Gateway-Versionen dürfen ``model`` weglassen).
        """
        expected = self._map_hermes_model(model)
        actual = str(echoed or "").strip()
        if actual and actual.casefold() != expected.casefold():
            raise ValueError(
                f"hermes: Gateway-Echo '{actual}' != gemapptes Zielmodell '{expected}' "
                f"(Benchmark-ID '{model}') — Antwort stammt nicht vom gemessenen Modell."
            )

    def _raise_on_hermes_failure(self, content: str, usage: Any) -> None:
        """Hermes-Fail-Fast-Signatur: HTTP 200 + Fehler-Content + usage=0 → RuntimeError.

        Der Gateway rendert Provider-/Auth-Fehler als normalen 200-Response
        (Fehler-Text als ``content``, ``usage`` komplett 0). Ohne diese Prüfung
        würde der Fehlertext als Benchmark-Antwort in die Results landen.
        """
        total_tokens = getattr(usage, "total_tokens", None) if usage else None
        if total_tokens == 0:
            raise RuntimeError(
                f"hermes: Gateway lieferte Fehler-Response ohne Token-Verbrauch "
                f"(Provider-/Auth-Fehler): {content[:300]}"
            )

    def _record_hermes_extras(self, response: Any) -> None:
        """Hermes-Extras (completed/partial/failed) + Session-ID in die Metadata."""
        extras = getattr(response, "hermes", None)
        if extras:
            self.last_response_metadata["hermes_extras"] = extras
        if getattr(response, "completed", None) is False:
            logger.warning("hermes: Run nicht komplett abgeschlossen (hermes.extras prüfen).")

    # ------------------------------------------------------------------
    # Accessibility & Modelle
    # ------------------------------------------------------------------

    def is_accessible(self) -> bool:
        """True wenn Gateway-Health ok und Probe-Completion gegen das Zielmodell läuft.

        Semantik (ARCHITECTURE.md): API erreichbar, aber Modellfehler → False
        mit Log-Befund statt silent Skip-Grund „Quota".
        """
        if not self._is_gateway_healthy():
            return False
        probe_model = self._probe_model_id()
        if probe_model is None:
            logger.error("hermes: keine Modelleinträge für is_accessible-Probe konfiguriert.")
            return False
        return self._probe_completion(probe_model)

    def _is_gateway_healthy(self) -> bool:
        """GET ``/health`` (public Route) — False bei Connection refused/HTTP-Fehler."""
        req = urllib_request.Request(f"{self._root_url()}/health")
        try:
            with urllib_request.urlopen(req, timeout=HEALTH_TIMEOUT_SEC) as resp:
                return resp.status == HTTP_OK
        except urllib_error.HTTPError as exc:
            logger.debug("hermes /health -> HTTP %d", exc.code)
            return False
        except (urllib_error.URLError, OSError) as exc:
            logger.debug("hermes /health nicht erreichbar: %s", exc)
            return False

    def _probe_completion(self, model: str) -> bool:
        """Minimale Probe-Completion gegen das gemappte Modell (authentifiziert).

        Läuft über ``_build_chat_params`` — nicht über ``_model_payload`` direkt:
        nur dieser Weg setzt die frische ``X-Hermes-Session-Id``. Ohne Header
        mappt der Gateway den Request per Fingerabdruck auf eine bestehende
        Session und die Probe würde History anhängen (AGENTS 2026-09-16).
        """
        try:
            payload = self._build_chat_params(model, "Hallo", None)
            payload["max_tokens"] = 32
            # Per-Request-Timeout (OpenAI-SDK): Der Haupt-Client trägt die
            # lange Lese-Wand (request_timeout, Default 2400 s) für Agent-Loop-
            # Tasks — die Accessibility-Probe darf damit nicht 40 min hängen.
            response = self.client.chat.completions.create(
                **payload, timeout=PROBE_TIMEOUT_SEC
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("hermes Probe-Completion fehlgeschlagen (model=%s): %s", model, exc)
            return False
        usage = getattr(response, "usage", None)
        if usage is not None and getattr(usage, "total_tokens", 0) == 0:
            logger.debug("hermes Probe: usage=0 (Gateway-Fehler-Response).")
            return False
        return bool(getattr(response, "choices", None))

    def get_available_models(self) -> list[str]:
        """Modell-IDs aus der Provider-Config (models-Block)."""
        models = self._get_provider_cfg().get("models") or []
        return [str(entry["id"]) for entry in models
                if isinstance(entry, dict) and entry.get("id")]
