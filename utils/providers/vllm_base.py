"""
Gemeinsame vLLM-Logik für lokale Provider-Klassen.

vLLM-Server werden über Shell-Skripte (``vllm-start`` / ``vllm-stop``)
fern­gesteuert (z. B. via SSH auf einer Workstation mit NVIDIA-GPU).
Das unterscheidet sich strukturell von llama.cpp:

- **Kein** eigener Build des Server-Cmd: das Skript ``vllm-start``
  entscheidet anhand des ``--config``-Parameters (Name oder Pfad einer
  TOML in ``~/ai/shared/configs/vllm/models/``), welches Modell geladen
  wird und mit welchen Server-Parametern.
- **Modell-Identität = TOML-Name**: ``model_id`` aus
  ``provider_config.yaml`` ist exakt der TOML-Dateiname (ohne ``.toml``)
  oder ein absoluter Pfad.
- **Ladezeit**: Modelle auf vLLM brauchen teils 10 Minuten (60B+ MoE);
  Default-Timeout ist 600 s, pro Modell überschreibbar.
- **Hardware-Einheit**: Eine Workstation kann nur ein Main-Modell
  gleichzeitig hosten; das Skript ``vllm-stop`` räumt den laufenden
  Main-Container ab, bevor ein neues Modell gestartet wird.

Elternklasse: ``BaseProviderClient`` aus ``utils/providers/base.py``.
Subklassen MÜSSEN ``PROVIDER_NAMES`` (Auto-Registry) und
``_PROVIDER_KEY`` (Config-Lookup) als Klassenattribute setzen.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
import shlex
from typing import Any

from utils.providers.base import BaseProviderClient

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


# HTTP-Statuscodes (vermeidet PLR2004 Magic-Value-Warnungen)
HTTP_OK: int = 200

# Default-Werte, falls die Config-Defaults fehlen.
DEFAULT_VLLM_PORT: int = 4300
DEFAULT_READY_TIMEOUT_SEC: int = 600  # 10 Min — Ladezeit großer MoE-Modelle
DEFAULT_POLL_SEC: int = 10
DEFAULT_PROBE_TIMEOUT_SEC: int = 30

# Standard OpenAI-Parameter, die direkt in den Request-Body geschrieben werden
# (vom OpenAI-Python-Client nativ akzeptiert). Sie werden NICHT in extra_body
# verpackt. Reihenfolge irrelevant — nur Membership zählt.
_OPENAI_STANDARD_SAMPLING_KEYS: tuple[str, ...] = ("temperature", "top_p")

# vLLM-spezifische Sampling-Extensions, die via ``extra_body`` geschleust werden
# MÜSSEN. Der OpenAI-Python-Client lehnt unbekannte kwargs in ``.create()``
# strikt ab (``Completions.create() got an unexpected keyword argument 'top_k'``);
# vLLM akzeptiert diese Felder aber nativ als JSON-Body. ``extra_body`` ist der
# offizielle Weg des OpenAI-Clients, provider-spezifische Felder zu schleusen.
# Siehe vLLM OpenAI-compatible server docs.
#
# Erweiterung (Session 2026-07-08): Bislang war nur ``top_k`` hardcodiert —
# dieselbe Bug-Klasse drohte bei jedem weiteren Sampling-Override. Die
# Whitelist macht die Auflösung generisch: neue vLLM-Extensions werden durch
# einen Eintrag hier bekannt, ohne dass ``_resolve_sampling`` angefasst werden
# muss (DRY, geschlossen gegen Mapping-Drift).
_VLLM_EXTRA_BODY_KEYS: tuple[str, ...] = (
    "top_k",
    "min_p",
    "repetition_penalty",
    "chat_template_kwargs",
    "guided_json",
    "guided_regex",
    "guided_choice",
    "guided_grammar",
    "guided_decoding_backend",
    "guided_whitespace_pattern",
    "bad_words",
    "stop_token_ids",
)


def _extract_port(base_url: str, default: int = DEFAULT_VLLM_PORT) -> int:
    """Port aus base_url parsen, Fallback auf default bei Parse-Fehler."""
    try:
        return urllib.parse.urlparse(base_url).port or default
    except (ValueError, AttributeError):
        return default


class VllmBaseClient(BaseProviderClient):
    """Provider-agnostische vLLM-Logik (Server-Lifecycle, OpenAI-Client, Query-Loop).

    Konkrete Subklassen (z. B. ``VllmSparkClient``) binden sich über
    ``PROVIDER_NAMES`` (Auto-Registry) und ``_PROVIDER_KEY`` (Config-Lookup)
    an genau einen Eintrag in ``providers.local.*`` aus ``provider_config.yaml``.

    Wichtig: ``PROVIDER_NAMES = []`` — die Basisklasse registriert sich NICHT
    selbst im Auto-Registry. Sie ist abstrakt in dem Sinne, dass eine
    direkte Instanziierung zu inkorrektem Provider-Lookup führt.
    """

    # Auto-Registry deaktiviert — nur Subklassen registrieren sich.
    PROVIDER_NAMES: list[str] = []

    # Klassenkonstante, die jede Subklasse überschreiben MUSS.
    # Bestimmt den Config-Key unter ``providers.local.*``.
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
        self._active_config: str | None = None  # TOML/Config des aktiven Modells (Profil-Tracking)
        self._server_model_name: str | None = None  # echter Server-Name (z. B. "ornith-1.0-35B-FP8")
        self._server_pid: int | None = None

    # ------------------------------------------------------------------
    # Config helpers (provider-key-fest, kein Runtime-Switch)
    # ------------------------------------------------------------------

    @property
    def _local_cfg(self) -> dict[str, Any]:
        """Gecachte Sicht auf ``providers.local``."""
        return self.config.get("providers", {}).get("local", {})

    def _provider_cfg(self) -> dict[str, Any]:
        """Provider-Config unter ``providers.local[_PROVIDER_KEY]`` lesen."""
        provider_cfg = self._local_cfg.get(self._PROVIDER_KEY, {})
        if provider_cfg:
            return provider_cfg
        # Defense-in-Depth: wenn _PROVIDER_KEY fehlt, sauberer leerer Dict
        # statt Fallback auf einen anderen Provider.
        return {}

    def _base_url(self) -> str:
        return self._provider_cfg().get("base_url", f"http://127.0.0.1:{DEFAULT_VLLM_PORT}/v1")

    def _api_key(self) -> str:
        """API-Key für den vLLM-Server.

        Unterstützt ``${VAR}``-Syntax: Wenn der Config-Wert mit ``$``
        beginnt, wird er als Environment-Variablen-Name interpretiert.
        Dies verhindert, dass API-Keys im Git-tracked Config-File
        stehen (CLAUDE.md: „API Keys NIEMALS in Git").
        """
        raw = self._provider_cfg().get("api_key", "sk-local")
        if isinstance(raw, str) and raw.startswith("${") and raw.endswith("}"):
            env_name = raw[2:-1]
            return os.environ.get(env_name, "sk-local")
        return raw

    def _server_start_cmd(self) -> str:
        """Komplettes Start-Kommando inkl. SSH-Wrapper.

        Wird rohwertig (shell=True) an subprocess übergeben. Die Config
        definiert den SSH-Aufruf samt ``vllm-start``-Invocation; der
        eigentliche Modell-Parameter wird erst zur Laufzeit von
        ``_build_server_cmd(model_id)`` angehängt.
        """
        return os.path.expanduser(
            self._provider_cfg().get("server_start_cmd", "vllm-start")
        )

    def _server_stop_cmd(self) -> str:
        """Komplettes Stop-Kommando inkl. SSH-Wrapper.

        Defense-in-Depth: Wenn das Kommando ``vllm-stop`` aufruft, wird
        ``--yes`` automatisch angehängt, sofern noch nicht vorhanden. Das
        Remote-Script verweigert sonst in nicht-interaktiven Umgebungen
        (Cron, Scripts, ``make benchmark-auto``) den Stop mit Exit != 0
        und löst eine Endlosschleife in :meth:`start_server` Pfad 2c aus.
        Die Config darf den Flag explizit setzen — er wird nicht doppelt
        angehängt.
        """
        cmd = os.path.expanduser(
            self._provider_cfg().get("server_stop_cmd", "vllm-stop")
        )
        if "vllm-stop" in cmd and "--yes" not in cmd:
            cmd = cmd.rstrip() + " --yes"
        return cmd

    def _server_root_url(self) -> str:
        """Base URL ohne /v1-Suffix, z. B. ``http://127.0.0.1:4300``."""
        return self._base_url().rstrip("/").removesuffix("/v1")

    def _health_url(self) -> str:
        return f"{self._server_root_url()}/health"

    def _chat_completions_url(self) -> str:
        return f"{self._server_root_url()}/v1/chat/completions"

    # ------------------------------------------------------------------
    # Model-Cfg-Lookup
    # ------------------------------------------------------------------

    def _model_cfg(self, model_id: str) -> dict[str, Any]:
        """Provider-Models-Config-Lookup mit Defense-in-Depth für ID-Varianten.

        vLLM verwendet TOML-Dateinamen als Modell-IDs. Die rohe Schreibweise
        aus ``provider_config.yaml`` (z. B. ``Qwen3.5-35B-A3B``) muss beim
        Lookup exakt treffen — ``resolve_canonical_model_id()`` kanonisiert
        die ID vor der Pipeline. Wir versuchen zuerst exakten Match,
        danach normalisierten Match (Punkt/Bindestrich → Underscore),
        damit beide Schreibweisen gefunden werden.
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

    @staticmethod
    def _normalize_model_name(model_id: str | None) -> str:
        """Punkt → Underscore, Bindestrich → Underscore, lowercased für Vergleich.

        Case-insensitive, damit ``Qwen3.5-35B-A3B`` (Config-Form, gemischt)
        und ``qwen3.5-35b-a3b`` (kanonisierte Pipeline-Form) denselben
        Normalisierungs-Hash haben. Verbesserung gegenüber dem älteren
        llama.cpp-Normalizer, der case-sensitive war und damit falsche
        Negativ-Treffer bei gemischten Modellnamen erzeugte.
        """
        if not model_id:
            return ""
        return model_id.lower().replace(".", "_").replace("-", "_")

    def _config_arg(self, model_id: str) -> str:
        """``--config <VALUE>``-Argument aus dem model-Cfg ableiten.

        Bevorzugung:
        1. ``model_cfg.config`` — absoluter Pfad zur TOML
        2. ``model_id`` — Name ohne ``.toml``-Endung (vllm-start-Skript
           erwartet diese Form)

        Der Lookup berücksichtigt die rohe Schreibweise zuerst, danach
        die kanonisierte Form. So funktionieren sowohl explizite Pfade
        als auch kanonisierte Modellnamen aus dem Pipeline-Eingang.
        """
        cfg = self._model_cfg(model_id)
        explicit = cfg.get("config")
        if explicit:
            return str(explicit)
        return model_id

    def _toml_models_dir(self) -> str:
        """Remote-Pfad zum Verzeichnis mit den vLLM-Modell-TOMLs.

        Default: ``~/ai/shared/configs/vllm/models/`` auf dem Remote-Host.
        Wird vom ``vllm-start``-Skript als Suchpfad für ``--config <NAME>``
        genutzt. Per Provider-Config (``toml_models_dir``) überschreibbar.
        """
        return self._provider_cfg().get("toml_models_dir", "~/ai/shared/configs/vllm/models/")

    def _vllm_defaults(self) -> dict[str, Any]:
        """vllm_defaults-Block aus ``providers.local.config`` (DRY-X).

        Initial leer (per Default) — bestehende vLLM-Modelle ohne
        Sampling-Override verhalten sich unverändert. Modelle mit
        explizitem ``model_cfg``-Override (Cross-Backend-Vergleich gegen
        llama.cpp, z. B. Ornith 1.0 35B) konsumieren diese Defaults als
        Cascade-Stufe zwischen ``model_cfg`` und dem Framework-Default
        (siehe :meth:`_resolve_sampling`).
        """
        return self._local_cfg.get("config", {}).get("vllm_defaults", {})

    def _resolve_sampling(
        self,
        model_id: str,
        passed_temperature: float | None,
    ) -> dict[str, Any]:
        """Sampling-Override-Kaskade: model_cfg > vllm_defaults > passed.

        Liefert die tatsächlich gesetzten Werte als flache Dict, die in
        ``query()`` per ``**`` in die ``params``-Dict gespreizt wird.

        Field-Klassifizierung:

        * **Standard OpenAI** (``temperature``, ``top_p``) — werden direkt
          in den Request-Body geschrieben, identisch zum OpenAI-HTTP-Schema.
        * **vLLM-spezifisch** (alle Keys aus :data:`_VLLM_EXTRA_BODY_KEYS`,
          z. B. ``top_k``, ``min_p``, ``repetition_penalty``,
          ``chat_template_kwargs``, ``guided_*``, ``bad_words``,
          ``stop_token_ids``) — werden in ``extra_body`` verpackt. Hintergrund:
          der OpenAI-Python-Client lehnt unbekannte kwargs in ``.create()``
          strikt ab (``Completions.create() got an unexpected keyword
          argument 'top_k'``); vLLM akzeptiert diese Felder aber nativ
          als JSON-Body. ``extra_body`` ist der offizielle Weg des
          OpenAI-Clients, provider-spezifische Felder zu schleusen.

        Chain (für jeden Key):
          * ``model_cfg`` > ``vllm_defaults`` > Framework-Default.
          * ``temperature`` fällt bei fehlendem Override auf
            ``passed_temperature`` (Framework, derzeit 0.1) zurück.
          * Alle anderen Keys: ``None`` heißt „nicht gesetzt" — der
            vLLM-Server-Default aus der Remote-TOML greift unverändert.

        Bei leerem ``vllm_defaults``-Block und ohne ``model_cfg``-Override
        verhält sich diese Methode exakt wie der vorherige Stand (nur
        ``temperature`` aus dem Aufrufer; kein extra_body).
        """
        cfg = self._model_cfg(model_id)
        defaults = self._vllm_defaults()
        out: dict[str, Any] = {}

        temp = self._resolve_temperature(cfg, defaults, passed_temperature)
        if temp is not None:
            out["temperature"] = temp

        self._resolve_top_p(cfg, defaults, out)
        self._resolve_vllm_extensions(cfg, defaults, out)
        return out

    @staticmethod
    def _resolve_temperature(
        cfg: dict[str, Any],
        defaults: dict[str, Any],
        passed_temperature: float | None,
    ) -> float | None:
        """temperature: gesonderter Pfad, weil passed_temperature als
        Framework-Fallback dient (die anderen Keys haben keinen solchen
        Fallback — dort bedeutet "nicht konfiguriert" = vLLM-TOML-Default).
        """
        temp = cfg.get("temperature", defaults.get("temperature"))
        if temp is not None:
            return temp
        return passed_temperature

    @staticmethod
    def _resolve_top_p(
        cfg: dict[str, Any],
        defaults: dict[str, Any],
        out: dict[str, Any],
    ) -> None:
        """top_p: Standard-OpenAI, direkt im Body (kein extra_body)."""
        top_p_value = cfg.get("top_p", defaults.get("top_p"))
        if top_p_value is not None:
            out["top_p"] = top_p_value

    @staticmethod
    def _resolve_vllm_extensions(
        cfg: dict[str, Any],
        defaults: dict[str, Any],
        out: dict[str, Any],
    ) -> None:
        """vLLM-Extensions: generische Whitelist-Schleife über
        ``_VLLM_EXTRA_BODY_KEYS``. Neue Extensions werden durch einen
        Eintrag in der Konstante bekannt — kein Code-Churn hier (DRY
        gegen Mapping-Drift, gleiche Bug-Klasse wie der ehemalige
        top_k-Only-Hack).
        """
        for ext_key in _VLLM_EXTRA_BODY_KEYS:
            value = cfg.get(ext_key, defaults.get(ext_key))
            if value is not None:
                out.setdefault("extra_body", {})[ext_key] = value

    def _discover_remote_tomls(self) -> list[str]:
        """TOML-Dateinamen (ohne Endung) vom Remote-Host listen.

        Wird per SSH über das gleiche ``server_start_cmd``-Präfix aufgerufen
        (``ssh ... 'ls <dir>'``). Resultat ist die kanonische Modell-Liste
        für diesen Provider — die TOML ist Source of Truth, nicht der
        ``providers.local.<key>.models``-Block.

        Bei Fehlern (kein SSH, kein Verzeichnis) wird eine leere Liste
        zurückgegeben; der Connector fällt dann auf die statische Config
        zurück.
        """
        start_cmd = self._server_start_cmd()
        # Wir extrahieren die "linke Seite" des SSH-Wrappers (alles bis
        # zum vllm-start-Aufruf) und hängen unseren ls-Befehl an.
        # Pattern: ``ssh -o ... user@host vllm-start`` → ``ssh -o ... user@host 'ls ...'``
        tokens = start_cmd.split()
        if not tokens or tokens[0] != "ssh":
            return []
        # Suche das Argument vor dem Remote-Befehl (typisch: letztes Token).
        remote_prefix = " ".join(tokens[:-1])
        target_dir = self._toml_models_dir()
        ssh_cmd = f"{remote_prefix} 'ls -1 {target_dir}*.toml 2>/dev/null'"
        try:
            proc = subprocess.run(
                ssh_cmd, shell=True, check=False,
                capture_output=True, text=True, timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.debug("TOML-Auto-Discovery SSH fehlgeschlagen: %s", exc)
            return []

        if proc.returncode != 0 or not proc.stdout:
            return []
        # Strippe .toml-Endung und Pfad-Anteile → reine Modell-Namen.
        names: list[str] = []
        for line in proc.stdout.splitlines():
            base = os.path.basename(line.strip()).removesuffix(".toml")
            if base:
                names.append(base)
        return names

    def _remote_chat_server_running(self) -> bool | None:
        """Prüft via SSH, ob ein vLLM-Chat-Server-Prozess läuft (nicht Embed).

        Bei Proxy-Setups liefert der Reverse-Proxy HTTP 502, sobald das
        Backend nicht antwortet — unabhängig davon, ob der vLLM-Prozess
        noch lädt oder komplett fehlt (Connection refused am Backend-Port).
        ``_probe_status()`` kann diese beiden Fälle NICHT unterscheiden,
        weil beide aus Sicht des Proxys 502 sind.

        Diese Methode schließt die Lücke, indem sie auf dem Remote-Host
        nach einem ``vllm serve``-Prozess sucht, der KEIN Embedding-Server
        ist (Embedding-Server starten mit ``--runner pooling``). So kann
        :meth:`start_server` Pfad 3.5 entscheiden, ob wirklich auf ein
        ladendes Backend gewartet wird oder ob ein Cold-Start nötig ist.

        Returns:
            True  — mindestens ein Chat-vLLM-Prozess läuft/lädt.
            False — kein Chat-vLLM-Prozess vorhanden (Backend wirklich down).
            None  — Prüfung nicht möglich (kein SSH-Setup oder SSH-Fehler);
                    Aufrufer muss konservativ warten (altes Verhalten).
        """
        start_cmd = self._server_start_cmd()
        tokens = start_cmd.split()
        if not tokens or tokens[0] != "ssh":
            return None
        remote_prefix = " ".join(tokens[:-1])
        # Embedding-Server ausschließen: sie laufen mit ``--runner pooling``.
        # ``pgrep -af`` listet PID + volle Kommandozeile; die beiden
        # ``grep -v`` filtern Embed-Instanz und den pgrep-Prozess selbst
        # heraus. Exit-Code 0 = Chat-Prozess gefunden, 1 = keiner da.
        ssh_cmd = (
            f"{remote_prefix} "
            "\"pgrep -af 'vllm serve' | grep -v -- '--runner pooling' | grep -v pgrep\""
        )
        try:
            proc = subprocess.run(
                ssh_cmd, shell=True, check=False,
                capture_output=True, text=True, timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.debug("SSH-Prozess-Check fehlgeschlagen: %s", exc)
            return None
        if proc.returncode == 0:
            return bool(proc.stdout.strip())
        if proc.returncode == 1:
            return False
        # Anderer Returncode (z. B. SSH 255 bei Verbindungsfehler) →
        # unsicher, konservativ warten statt fälschlich neu zu starten.
        logger.debug(
            "SSH-Prozess-Check unsicher (returncode=%d, stderr=%s)",
            proc.returncode, proc.stderr.strip(),
        )
        return None

    def _backend_stopped(self) -> bool:
        """Prüfe, ob das vLLM-Backend nach ``stop_server()`` wirklich down ist.

        Bei Proxy-Setups (permanenter Reverse-Proxy auf Port 4300) liefert
        der Proxy HTTP 502, sobald das Backend weg ist — ``_probe_status()``
        gibt dann ``"loading"`` zurück, NIEMALS ``"down"``. Ein reiner
        ``_probe_status() == "down"``-Check würde den Stop also immer
        fälschlich als fehlgeschlagen melden.

        Diese Methode schließt die Lücke: bei ``"down"`` gilt der Stop als
        erfolgreich (kein Proxy oder Proxy ebenfalls weg). Bei ``"loading"``
        wird per SSH geprüft, ob noch ein Chat-vLLM-Prozess läuft — nur wenn
        KEIN Prozess mehr existiert (``_remote_chat_server_running() is
        False``), gilt der Stop als erfolgreich. Bei ``None`` (SSH-Check
        nicht möglich) wird konservativ ``False`` zurückgegeben (Aufrufer
        meldet Fehler, wie bisher).
        """
        status = self._probe_status()
        if status == "down":
            return True
        if status == "loading":
            chat_running = self._remote_chat_server_running()
            if chat_running is False:
                logger.debug(
                    "Backend-Stopp verifiziert: Proxy meldet 'loading' (502), "
                    "aber kein vLLM-Chat-Prozess mehr aktiv (SSH-Check)."
                )
                return True
        return False

    # ------------------------------------------------------------------
    # Health- und Readiness-Checks
    # ------------------------------------------------------------------

    def _is_healthy(self) -> bool:
        """Returns True when the ``/health`` endpoint responds with HTTP 200.

        Delegiert an ``_probe_status()``, um Code-Duplikation zu vermeiden
        (beide Methoden bauen denselben Request mit Bearer-Token und
        10-s-Timeout). ``_probe_status()`` liefert zusätzlich die
        Unterscheidung zwischen 'loading' (Proxy 502) und 'down'
        (Connection refused), die ``start_server()`` für die
        Pfad-Auswahl benötigt.
        """
        return self._probe_status() == "healthy"

    def _probe_status(self) -> str:
        """Differenziert zwischen 'healthy', 'loading' und 'down'.

        WICHTIG für Proxy-Setups: Ein Reverse-Proxy (z. B. Token-Capture-
        Proxy auf Port 4300) gibt HTTP 502 zurück, wenn der Backend-vLLM-
        Server noch lädt. Der Connector darf das NICHT als „Server nicht
        gestartet" interpretieren und ``vllm-start`` aufrufen — sonst
        wird der ladende Container gestoppt und neu gestartet (5-10 Min
        Modell-Ladezeit verschwendet).

        Rückgabe:
        - ``"healthy"``: /health → 200, Server bereit
        - ``"loading"``: /health → 502 (Proxy erreicht, Backend lädt)
          oder /health → 200 mit vLLM-Loading-Status
        - ``"down"``: Verbindung komplett fehlgeschlagen (Connection
          refused, DNS-Fehler, etc.)
        """
        req = urllib.request.Request(
            self._health_url(),
            headers={"Authorization": f"Bearer {self._api_key()}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == HTTP_OK:
                    return "healthy"
                return "loading"
        except urllib.error.HTTPError as exc:
            # 502/503 = Proxy erreicht, aber Backend nicht bereit (lädt noch)
            if exc.code in (502, 503):
                return "loading"
            # 401/403 = Auth-Problem (Token-Rotation, Rate-Limit, Probe-Race).
            # Als "loading" behandeln — verhindert unnötigen Server-Restart bei
            # transienten Auth-Issues. Bei dauerhaft falschem Token läuft der
            # start_server-Timeout ins Leere, was sicherer ist als ein
            # fälschlicher Server-Kill.
            if exc.code in (401, 403):
                return "loading"
            return "down"
        except (urllib.error.URLError, OSError):
            return "down"

    def _is_model_ready(self, model_id: str) -> bool:
        """Run a tiny completion probe so benchmark starts only when model is responsive.

        WICHTIG: vLLM 0.22.1 nutzt ``"reasoning"`` als Feldname (nicht
        ``"reasoning_content"`` wie der OpenAI-Standard). Wir prüfen beide.

        Für Reasoning-Modelle (z. B. Ornith 1.0 35B) ist ``max_tokens=8`` zu
        klein — das Modell steckt im Reasoning fest und ``content`` bleibt
        ``null``. Wir nutzen ``max_tokens=32`` als sicheren Default, der
        genug Raum für eine kurze Reasoning-Phase + Antwort lässt.

        Model-Name-Fallback: Wenn der Probe mit ``model_id`` (normalisiert,
        z. B. "ornith-1_0-35B-FP8") fehlschlägt, weil der Server das Modell
        unter einem anderen Namen kennt (z. B. "ornith-1.0-35B-FP8"), wird
        automatisch ``/v1/models`` abgefragt und mit dem Server-Namen erneut
        probiert. Der gefundene Server-Name wird in ``_server_model_name``
        gespeichert für spätere API-Calls.
        """
        result, resolved_name = self._probe_model_ready(model_id)
        if result and resolved_name:
            self._server_model_name = resolved_name
        return result

    def _probe_model_ready(self, model_id: str) -> tuple[bool, str | None]:
        """Intern: Probe-Chat senden, bei Name-Mismatch Server-Namen abfragen.

        Returns:
            (True, server_name) wenn Modell bereit.
            (False, None) wenn nicht.
        """
        ok = self._send_probe(model_id)
        if ok:
            return True, model_id

        # Model-Name-Mismatch? Server-Namen abfragen und erneut probieren.
        detected = self._query_active_model()
        if detected and detected != model_id:
            logger.debug(
                "Probe mit '%s' fehlgeschlagen — erneut mit Server-Namen '%s'",
                model_id, detected,
            )
            ok = self._send_probe(detected)
            if ok:
                return True, detected

        return False, None

    def _send_probe(self, model_name: str) -> bool:
        """Sende einen einzelnen Hallo-Probe-Request an das Modell."""
        prov_cfg = self._provider_cfg()
        probe_timeout_sec = max(5, int(prov_cfg.get("server_ready_probe_timeout_sec", DEFAULT_PROBE_TIMEOUT_SEC)))
        probe_url = self._chat_completions_url()
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Hallo"}],
            "max_tokens": 32,
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
                # vLLM 0.22.1: "reasoning", OpenAI-Standard: "reasoning_content"
                reasoning_content = (
                    (message.get("reasoning_content") or "")
                    or (message.get("reasoning") or "")
                ).strip()
                finish_reason = (choice0.get("finish_reason") or "").strip()
                usage = body.get("usage") or {}
                total_tokens = usage.get("total_tokens") or 0
                return bool(visible_content or reasoning_content or finish_reason or total_tokens > 0)
        except urllib.error.HTTPError as exc:
            self._log_probe_failure("HTTP", probe_url, probe_timeout_sec, exc, model_name)
            return False
        except urllib.error.URLError as exc:
            self._log_probe_failure("transport", probe_url, probe_timeout_sec, exc.reason, model_name)
            return False
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self._log_probe_failure("parse/runtime", probe_url, probe_timeout_sec, exc, model_name)
            return False

    def _log_probe_failure(
        self,
        kind: str,
        probe_url: str,
        timeout_sec: int,
        exc: Any,
        model_id: str,
    ) -> None:
        """Einheitliches Debug-Logging für Readiness-Probe-Fehler."""
        logger.debug(
            "Readiness probe %s error (provider=%s, model=%s, url=%s, timeout=%ss): %s",
            kind, self._PROVIDER_KEY, model_id, probe_url, timeout_sec, exc,
        )

    def _query_active_model(self) -> str | None:
        """Ask the running server which model it currently serves (via ``/v1/models``).

        WICHTIG: Der Token-Capture-Proxy auf Port 4300 authentifiziert
        JEDEN Request — auch ``/v1/models``. Ohne Bearer-Token gibt der
        Proxy 401 zurück, was fälschlicherweise als „kein Modell aktiv"
        interpretiert wird. Das führt dazu, dass ``start_server()`` den
        laufenden Server stoppt und neu startet (fataler Bug).
        """
        try:
            models_url = f"{self._server_root_url()}/v1/models"
            req = urllib.request.Request(
                models_url,
                headers={"Authorization": f"Bearer {self._api_key()}"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
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

    def _build_server_cmd(self, model_id: str) -> str:
        """Vollständigen vllm-start-Befehl für die gegebene Modell-ID bauen.

        Im Gegensatz zu llama.cpp werden hier KEINE Sampling-Parameter
        angehängt — die liegen in der TOML. Wir reichen nur ``--config``
        und optional ``--gpu-mem`` (Ressourcen-Override) durch.

        ``server_start_cmd`` ist bereits der vollständige SSH-Wrapper
        (z. B. ``ssh ... 'vllm-start'``); wir hängen die Argumente als
        Shell-String an. Alle interpolierten Werte werden mit
        ``shlex.quote()`` abgesichert, um Shell-Injection über
        konfigurierte Modell-Namen oder extra_args zu verhindern.
        """
        start_cmd = self._server_start_cmd()
        config_arg = self._config_arg(model_id)

        cmd = f"{start_cmd} --config {shlex.quote(config_arg)}"

        # gpu_memory_utilization als Ressourcen-Override (provider- oder
        # per-Modell-Override). Modell-Eintrag gewinnt gegen Provider.
        cfg = self._model_cfg(model_id)
        gpu_mem = cfg.get("gpu_mem_utilization")
        if gpu_mem is None:
            gpu_mem = self._provider_cfg().get("gpu_mem_utilization")
        if gpu_mem is not None:
            cmd += f" --gpu-mem {shlex.quote(str(gpu_mem))}"

        # Per-Modell extra_args (z. B. für Embed-Instanzen oder Test-Hooks).
        extra = cfg.get("extra_server_args", [])
        if isinstance(extra, list):
            for arg in extra:
                if isinstance(arg, str) and arg.strip():
                    cmd += f" {shlex.quote(arg.strip())}"

        return cmd

    # ------------------------------------------------------------------
    # OpenAI-Client (lazy-loaded, recreated on base_url change)
    # ------------------------------------------------------------------

    @property
    def client(self) -> Any:
        """Lazy-load the OpenAI-compat client pointing at the vLLM server.

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
        read_timeout = float(prov_cfg.get("read_timeout", 600.0))
        timeout_cfg = httpx.Timeout(connect=10.0, read=read_timeout, write=300.0, pool=300.0)
        limits = httpx.Limits(max_keepalive_connections=0, max_connections=10)
        http_client = httpx.Client(timeout=timeout_cfg, limits=limits)
        self._client = OpenAI(
            base_url=current_base_url,
            api_key=self._api_key(),
            http_client=http_client,
            max_retries=1,
        )
        self._client_base_url = current_base_url
        return self._client

    # ------------------------------------------------------------------
    # Server-Lifecycle
    # ------------------------------------------------------------------

    def is_server_running(self) -> bool:
        """Returns True when the vLLM ``/health`` endpoint responds with 200."""
        return self._is_healthy()

    def _wait_for_model_ready(
        self,
        model_id: str | None,
        *,
        timeout_sec: int,
        poll_sec: int,
        log_prefix: str,
    ) -> bool:
        """Polle /health + Readiness-Probe, bis Server modellbereit oder Timeout.

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
        """Start the vLLM server for the given model id (TOML-Name oder Pfad).

        Falls der Server bereits mit einem ANDEREN Modell läuft, wird er
        gestoppt und neu gestartet (entspricht swap_model). Der
        Server-Start wird über das in der Config definierte
        ``server_start_cmd`` (typischerweise ``ssh ... 'vllm-start'``)
        angestoßen — die TOML-Auswahl passiert durch ``--config``.

        WICHTIG — Proxy-Loading-Erkennung:
        Wenn ein Reverse-Proxy (z. B. Token-Capture-Proxy) vor dem vLLM-
        Server liegt und HTTP 502 zurückgibt, bedeutet das „Backend lädt
        noch" — NICHT „Server nicht gestartet". In diesem Fall wird auf
        Readiness gewartet, ohne ``vllm-start`` aufzurufen. Erst bei
        echter Verbindungsunfähigkeit (``"down"``) wird gestartet.

        Args:
            model_id: TOML-Name (ohne Endung) oder absoluter Pfad. None
                startet das Default-Modell aus ``VLLM_ACTIVE_CONFIG``
                (Default-Verhalten des ``vllm-start``-Skripts).

        Returns:
            True bei erfolgreichem Start, False sonst.
        """
        status = self._probe_status()
        healthy = (status == "healthy")
        probe_name = self._server_model_name or model_id

        # Pfad 1/1b: Server läuft bereits mit dem gewünschten Modell.
        if healthy and self._active_model and self._active_model == model_id and model_id:
            return self._start_already_running(model_id, probe_name)

        # Pfad 2: Server gesund, aber kein _active_model gesetzt → adoptieren.
        if healthy and self._active_model is None and model_id:
            return self._start_adopt(model_id)

        # Pfad 3: Server läuft mit einem ANDEREN bekannten Modell → Restart.
        if healthy and self._active_model and self._active_model != model_id:
            return self._start_swap_restart(model_id)

        # Pfad 3.5/4: Proxy-Loading abwarten oder Cold-Start.
        return self._start_loading_or_cold(model_id, status)

    def _start_already_running(self, model_id: str, probe_name: str) -> bool:
        """Pfad 1/1b: Server gesund + aktives Modell = Zielmodell.

        Pfad 1: Readiness-Probe erfolgreich → sofort zurück.
        Pfad 1b: Probe transient fehlgeschlagen → 3× retry (je 2 s).
        Kein Durchfallen zum Cold-Start — das würde den laufenden Server
        neu starten (5-10 Min verschwendet).
        """
        if self._is_model_ready(probe_name):
            logger.debug("vLLM server already running at %s", self._base_url())
            return True
        for retry in range(3):
            time.sleep(2)
            if self._is_model_ready(probe_name):
                logger.debug(
                    "vLLM probe succeeded on retry %d (model=%s)", retry + 1, model_id,
                )
                return True
        warning = (
            f"vLLM server at {self._base_url()} is healthy with model '{model_id}', "
            "but readiness probe failed 3 times. Benchmark wird beendet."
        )
        logger.warning(warning)
        print(f"   ⚠️  {warning}")
        return False

    def _start_adopt(self, model_id: str) -> bool:
        """Pfad 2: Server gesund, _active_model None → laufenden Server adoptieren.

        Unterpfade:
        - 2a: Server meldet Zielmodell → adoptieren (ggf. mit Warmup-Wartezeit).
        - 2b: /v1/models nicht ermittelbar, aber Probe erfolgreich → adoptieren.
        - 2c: Server meldet ANDERES Modell → Stop + rekursiver Neustart.
        - 2d: Server gesund, aber Modell nicht ansprechbar → Fehler (nicht stoppen).
        """
        detected = self._query_active_model()

        # Pfad 2a: Server meldet das gewünschte Modell → adoptieren.
        # WICHTIG: Für API-Calls (Probe, Query) muss der Server-Modellname
        # (detected) verwendet werden, nicht der normalisierte model_id.
        if detected and self._adopt_matches(detected, model_id):
            return self._adopt_with_warmup(model_id, detected)

        # Pfad 2b: /v1/models nicht ermittelbar (detected=None) → direkt
        # adoptieren, wenn das Modell auf einen Probe-Request antwortet.
        # Verhindert, dass ein temporärer /v1/models-Fehler (z. B. Proxy-
        # Latenz) zum Stoppen des laufenden Servers führt.
        if detected is None and self._is_model_ready(model_id):
            self._mark_active(model_id)
            logger.debug(
                "Adopting already running vLLM endpoint at %s with model '%s' "
                "(model list unavailable, probe succeeded)",
                self._base_url(), model_id,
            )
            return True

        # Pfad 2c: ECHTER Endpoint-Konflikt — Server meldet ein ANDERES
        # Modell. Nur in diesem Fall darf der Server gestoppt werden.
        if detected and not self._adopt_matches(detected, model_id):
            warning = (
                f"OpenAI-kompatibler Endpunkt unter {self._base_url()} ist bereits aktiv "
                f"(aktives Modell: {detected}). Starte Server mit '{model_id}' neu..."
            )
            logger.warning(warning)
            print(f"   ⚠️  {warning}")
            if not self._stop_and_verify():
                error = (
                    f"vLLM-Server unter {self._base_url()} konnte nicht gestoppt werden "
                    f"(Status nach stop_server(): {self._probe_status()}). "
                    "Manueller Eingriff erforderlich — Benchmark wird beendet."
                )
                logger.error(error)
                print(f"   ❌ {error}")
                return False
            return self.start_server(model_id)

        # Pfad 2d: detected=None UND Probe fehlgeschlagen → Server
        # scheinbar gesund, aber Modell nicht ansprechbar. NICHT
        # stoppen — als Fehler melden.
        warning = (
            f"OpenAI-kompatibler Endpunkt unter {self._base_url()} ist gesund, "
            f"aber Modell '{model_id}' antwortet nicht auf Probe-Request. "
            "Benchmark wird beendet."
        )
        logger.warning(warning)
        print(f"   ⚠️  {warning}")
        return False

    def _adopt_with_warmup(self, model_id: str, detected: str) -> bool:
        """Pfad 2a: Server läuft bereits mit passendem Modell — adoptieren.

        Bei noch nicht schlagfertigem Modell wird auf Readiness gewartet
        (Adopt-Warmup). Der Server-Name (``detected``) wird für alle
        nachfolgenden API-Calls genutzt.
        """
        probe_name = detected  # Server-Name für API-Calls
        if self._is_model_ready(probe_name):
            self._mark_active(model_id, detected)
            logger.debug(
                "Adopting already running vLLM endpoint at %s with model '%s' (server name: '%s')",
                self._base_url(), model_id, detected,
            )
            return True

        prov_cfg = self._provider_cfg()
        adopt_timeout = int(prov_cfg.get(
            "existing_server_ready_timeout_sec",
            prov_cfg.get("server_ready_timeout_sec", DEFAULT_READY_TIMEOUT_SEC),
        ))
        adopt_poll = int(prov_cfg.get("server_ready_poll_sec", DEFAULT_POLL_SEC))
        print(
            f"   ⏳ Server läuft bereits mit '{detected}' — "
            f"warte auf Modell-Bereitschaft (Timeout: {adopt_timeout}s) ...",
            flush=True,
        )
        if self._wait_for_model_ready(
            probe_name, timeout_sec=adopt_timeout, poll_sec=adopt_poll,
            log_prefix="Adopt warmup",
        ):
            self._mark_active(model_id, detected)
            print("   ✅ Modell bereit nach Wartezeit", flush=True)
            logger.debug(
                "Adopted already running vLLM endpoint at %s with model '%s' (server name: '%s')",
                self._base_url(), model_id, detected,
            )
            return True

        warning = (
            f"OpenAI-kompatibler Endpunkt unter {self._base_url()} läuft bereits mit '{detected}', "
            "antwortet aber auch nach Wartezeit noch nicht stabil auf den Hallo-Probe-Request. "
            "Benchmark wird beendet."
        )
        logger.warning(warning)
        print(f"   ⚠️  {warning}")
        return False

    def _start_swap_restart(self, model_id: str) -> bool:
        """Pfad 3: Server läuft mit anderem bekannten Modell → Stop + Restart."""
        logger.debug(
            "vLLM server running with managed model '%s', restarting for '%s'",
            self._active_model, model_id,
        )
        if not self._stop_and_verify():
            error = (
                f"vLLM-Server (Modell '{self._active_model}') konnte nicht gestoppt "
                f"werden (Status nach stop_server(): {self._probe_status()}). "
                "Manueller Eingriff erforderlich — Benchmark wird beendet."
            )
            logger.error(error)
            print(f"   ❌ {error}")
            return False
        return self.start_server(model_id)

    def _stop_and_verify(self) -> bool:
        """Server stoppen und Backend-Down verifizieren (Shared-Helper).

        Gemeinsam für Pfad 2c (Endpoint-Konflikt) und Pfad 3 (Swap).
        Returns True wenn das Backend wirklich down ist, False wenn der
        Stop fehlschlug. Die Fehlermeldung wird vom Aufrufer gesetzt —
        sie unterscheidet sich zwischen den Pfaden (Rekursionsschutz:
        bei False bricht der Aufrufer ab statt ``start_server`` erneut
        aufzurufen).
        """
        self.stop_server()
        time.sleep(2)
        return self._backend_stopped()

    def _start_loading_or_cold(self, model_id: str | None, status: str) -> bool:
        """Pfad 3.5/4: Proxy-Loading abwarten oder Cold-Start.

        Pfad 3.5: Proxy meldet ``"loading"`` (502). Ein Reverse-Proxy
        gibt 502 sowohl zurück, wenn das Backend lädt, ALS AUCH wenn gar
        kein vLLM-Prozess läuft (Connection refused am Backend-Port).
        Ohne Differenzierung würde der Connector hier 600 s auf ein
        nicht existierendes Backend warten. Per SSH wird geprüft, ob ein
        Chat-Server-Prozess existiert — nur dann wird gewartet, sonst
        Cold-Start (Pfad 4).
        """
        if status == "loading" and model_id:
            chat_running = self._remote_chat_server_running()
            if chat_running is not False:
                return self._start_wait_for_loading(model_id)
            # chat_running is False: Proxy-502 ist ein Down-Backend, kein
            # ladender Prozess → Cold-Start (Pfad 4) statt Wartezeit.
            logger.info(
                "Proxy meldet 502, aber kein vLLM-Chat-Prozess aktiv "
                "→ Cold-Start statt Wartezeit (vermeidet 600-s-Timeout)."
            )
            print(
                "   ⚠️  Proxy meldet 502, aber kein vLLM-Chat-Prozess gefunden "
                "— starte Server neu (Cold-Start) ...",
                flush=True,
            )
            # Durchfallen zu Pfad 4 (Cold-Start).
        return self._cold_start(model_id)

    def _start_wait_for_loading(self, model_id: str) -> bool:
        """Pfad 3.5 (Warte-Zweig): Backend lädt noch — auf Readiness warten."""
        prov_cfg = self._provider_cfg()
        loading_timeout = int(prov_cfg.get(
            "existing_server_ready_timeout_sec",
            prov_cfg.get("server_ready_timeout_sec", DEFAULT_READY_TIMEOUT_SEC),
        ))
        loading_poll = int(prov_cfg.get("server_ready_poll_sec", DEFAULT_POLL_SEC))
        print(
            f"   ⏳ vLLM-Backend lädt noch (Proxy meldet 502) — "
            f"warte auf Readiness (Timeout: {loading_timeout}s) ...",
            flush=True,
        )
        if self._wait_for_model_ready(
            model_id, timeout_sec=loading_timeout, poll_sec=loading_poll,
            log_prefix="Loading warmup",
        ):
            detected = self._query_active_model()
            self._mark_active(model_id, detected)
            print("   ✅ Backend bereit nach Wartezeit", flush=True)
            return True
        logger.error("vLLM backend did not become ready within %d s (loading).", loading_timeout)
        return False

    def _cold_start(self, model_id: str | None) -> bool:
        """Pfad 4: vllm-start launchen und auf Readiness warten."""
        cmd = self._build_server_cmd(model_id) if model_id else self._server_start_cmd()
        logger.debug("Starting vLLM server: %s", cmd)
        print(f"   ⏳ Starte vLLM Server ({model_id}) ...")
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
            logger.error("Failed to launch vLLM server: %s", exc)
            return False

        prov_cfg = self._provider_cfg()
        # Per-Modell-Override hat Vorrang: große MoE-Modelle brauchen
        # länger als den Provider-Default (600 s).
        _mcfg = self._model_cfg(model_id) if model_id else {}
        ready_timeout = int(
            _mcfg.get("ready_timeout_sec")
            or prov_cfg.get(
                "existing_server_ready_timeout_sec",
                prov_cfg.get("server_ready_timeout_sec", DEFAULT_READY_TIMEOUT_SEC),
            )
        )
        ready_poll = int(prov_cfg.get("server_ready_poll_sec", DEFAULT_POLL_SEC))
        if self._wait_for_model_ready(
            model_id, timeout_sec=ready_timeout, poll_sec=ready_poll, log_prefix="vLLM",
        ):
            detected = self._query_active_model()
            self._mark_active(model_id, detected)
            print(f"   ✅ Server bereit ({ready_timeout}s)")
            logger.debug("vLLM server ready within %d s", ready_timeout)
            return True
        logger.error("vLLM server did not become ready within %d s.", ready_timeout)
        return False

    def _mark_active(self, model_id: str, server_name: str | None = None) -> None:
        """Aktives Modell + Config + Server-Namen nach Start/Adopt setzen.

        Shared-Helper für alle Start-Pfade, die ein Modell erfolgreich
        aktiviert haben (Pfad 2a/2b/3.5/4). Vermeidet wiederholte
        3-Zeilen-Assignments (DRY). ``server_name=None`` fällt auf
        ``model_id`` zurück (Pfad 2b: kein Server-Name bekannt).
        """
        self._active_model = model_id
        self._active_config = self._config_arg(model_id)
        self._server_model_name = server_name or model_id

    def _adopt_matches(self, detected: str, model_id: str) -> bool:
        """Prüfe, ob das vom Server gemeldete Modell dem gewünschten entspricht.

        vLLM liefert Modell-IDs im Stil ``/path/to/model`` oder
        ``org/model-name``. Wir matchen tolerant per Substring auf der
        kanonisierten Form.

        WICHTIG — Thinking-Profile: Zwei Profile (Standard + Thinking)
        zeigen auf dasselbe TOML (``config`` identisch), haben aber
        unterschiedliche ``model_id``s (z. B. ``qwen3_6-35b-a3b-nvfp4``
        vs. ``qwen3_6-35b-a3b-nvfp4-thinking``). Der Server meldet den
        TOML-Basisnamen (z. B. ``Qwen3.6-35B-NVFP4``). Ein reiner
        model_id-Substring-Match schlägt hier fehl, weil die model_id
        zusätzliche Segmente enthält (``a3b``, ``thinking``), die im
        TOML-Namen nicht vorkommen. Daher wird ZUSÄTZLICH der
        Config-Name (``_config_arg``) gegen ``detected`` geprüft —
        stimmt dieser überein, handelt es sich um dasselbe Backend und
        ein Profil-Wechsel darf KEIN Stop+Restart auslösen.
        """
        def _strip(value: str) -> str:
            return value.lower().replace(".", "").replace("-", "").replace("_", "").replace("/", "")

        def _match(a: str, b: str) -> bool:
            sa, sb = _strip(a), _strip(b)
            return bool(sa) and bool(sb) and (sa in sb or sb in sa)

        if _match(detected, model_id):
            return True
        # Config/TOML-Name als zweite Match-Ebene — schließt Thinking-
        # Profile ein, deren model_id den TOML-Namen nicht substring-
        # enthält (z. B. a3b-MoE-Notation, -thinking-Suffix).
        config_name = self._config_arg(model_id)
        if config_name and config_name != model_id and _match(detected, config_name):
            logger.debug(
                "Adopt-Match via config-Name: detected='%s' matched config='%s' "
                "(model_id='%s') — Profil-Wechsel ohne Server-Swap.",
                detected, config_name, model_id,
            )
            return True
        return False

    def stop_server(self) -> None:
        """Stop the vLLM server via the configured stop command."""
        if self._server_pid is not None:
            logger.debug("Stopping vLLM server (PID %d)", self._server_pid)
            try:
                subprocess.run(["kill", str(self._server_pid)], check=False)
            except OSError as exc:
                logger.warning("Could not kill PID %d: %s", self._server_pid, exc)
            self._server_pid = None

        cmd = self._server_stop_cmd()
        logger.debug("Stopping vLLM server via stop command: %s", cmd)
        try:
            subprocess.run(cmd, shell=True, check=False)
        except OSError as exc:
            logger.warning("Could not stop vLLM server: %s", exc)

        self._active_model = None
        self._active_config = None
        self._server_model_name = None
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
        """Stop current server and restart it with the new model.

        WICHTIG: Nach ``stop_server()`` wird aktiv auf Backend-Down
        gewartet (``_backend_stopped()``), bevor ``start_server()``
        aufgerufen wird. Ohne dieses Polling könnte ``start_server()``
        den noch laufenden alten Prozess sehen (SSH-Latenz, langsamer
        Shutdown) und über Pfad 2c rekursiv ``stop_server()`` aufrufen —
        bis zum Python-Recursion-Limit. Bei permanentem Proxy liefert
        ``_probe_status()`` ``"loading"`` statt ``"down"``; die SSH-
        Prozess-Prüfung in ``_backend_stopped()`` schließt diese Lücke.
        """
        logger.debug("Swapping vLLM model to: %s", model_id)
        self.stop_server()

        if self._provider_cfg().get("server_post_stop_cmd"):
            print("   🧹 Cache-Cleanup nach Modell-Wechsel...")
            self._run_cleanup()
            time.sleep(3)
        else:
            time.sleep(2)

        # Auf tatsächliches Herunterfahren warten (max 30 s), sonst
        # würde start_server() den alten Container sehen und rekursiv
        # stop_server() aufrufen. Bei permanentem Proxy liefert
        # _probe_status() "loading" statt "down" — _backend_stopped()
        # prüft dann per SSH, ob der vLLM-Prozess wirklich weg ist.
        for _ in range(15):
            if self._backend_stopped():
                break
            time.sleep(2)

        return self.start_server(model_id)

    # ------------------------------------------------------------------
    # BaseProviderClient interface
    # ------------------------------------------------------------------

    def is_accessible(self) -> bool:
        """Returns True when the ``/health`` endpoint is reachable."""
        return self._is_healthy()

    def _ensure_model_ready(self, model: str) -> bool:
        """Stellt sicher, dass ``model`` auf dem vLLM-Server geladen ist.

        Profil-Sprung-Logik: Zwei Profile (Standard + Thinking) zeigen auf
        dasselbe TOML (``config`` identisch). In diesem Fall darf KEIN
        Container-Swap erfolgen — nur die per-Request-Sampling-Parameter
        wechseln (``_resolve_sampling`` greift automatisch auf das
        model_cfg des neuen Profils zu). Der Vergleich erfolgt auf der
        ``_config_arg``-Ebene (TOML/Pfad), NICHT auf der model_id.

        Returns:
            True wenn Modell bereit (oder bereits geladen), sonst False.
        """
        # Aktives Modell stimmt → Re-Validierung gegen Server (Stale-Ready-Schutz)
        if self._active_model and self._active_model == model:
            # _server_model_name für API-Calls nutzen (z. B. "ornith-1.0-35B-FP8"
            # statt normalisiertem "ornith-1_0-35B-FP8")
            probe_name = self._server_model_name or model
            if self._is_healthy() and self._is_model_ready(probe_name):
                return True
            logger.debug(
                "Stale-Ready erkannt: _active_model='%s' aber Server nicht erreichbar "
                "oder Modell nicht bereit — Neustart.",
                model,
            )
            self._active_model = None
            self._active_config = None
            self._server_model_name = None
            return self.start_server(model)

        # Profil-Wechsel: anderes Profil (Standard ↔ Thinking), aber
        # DASSELBE TOML. Kein Container-Swap nötig — nur per-Request-Sampling
        # wechselt. Backward-compat: ohne aktives _active_config (ältere
        # Single-Profile-Connector-Instanzen) wird der bisherige Pfad benutzt.
        if (
            self._active_model is not None
            and self._active_model != model
            and self._active_config is not None
            and self._active_config == self._config_arg(model)
        ):
            probe_name = self._server_model_name or self._active_model
            if self._is_healthy() and self._is_model_ready(probe_name):
                self._active_model = model
                self._active_config = self._config_arg(model)
                logger.debug(
                    "Profil-Wechsel ohne Container-Swap: '%s' → '%s' "
                    "(gleiches TOML '%s').",
                    self._active_model, model, self._active_config,
                )
                return True
            logger.debug(
                "Profil-Wechsel erkannt, aber Server nicht bereit — Cold-Start.",
            )
            self._active_model = None
            self._active_config = None
            self._server_model_name = None
            return self.start_server(model)

        if self._active_model is None:
            return self.start_server(model)
        return self.swap_model(model)

    def _build_messages(self, prompt: str, system_prompt: str | None) -> list[dict[str, str]]:
        """Chat-Messages-Liste mit optionalem System-Prompt bauen."""
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
        """Content + Reasoning aus OpenAI-kompatibler Response extrahieren.

        Setzt ``self.last_response_metadata`` mit allen beobachtbaren Feldern.

        vLLM 0.22.1 nutzt ``reasoning`` als Feldname (nicht ``reasoning_content``
        wie der OpenAI-Standard). Wir prüfen beide.
        """
        msg = response.choices[0].message if response.choices else None
        content = (msg.content or "") if msg else ""
        reasoning = (
            (getattr(msg, "reasoning_content", None) or "")
            or (getattr(msg, "reasoning", None) or "")
        ) if msg else ""

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
            self._apply_reasoning_fallback(
                getattr(response, "usage", None), content, reasoning
            )
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
        """Send a chat completion request to the vLLM server.

        Automatisches Model-Swapping, wenn ``model`` vom aktiven Modell abweicht.
        """
        if not self._ensure_model_ready(model):
            raise RuntimeError(
                f"vLLM endpoint conflict or startup failure for model '{model}'"
            )

        # Client nach langen Queries zurücksetzen, um Connection-Leaks zu verhindern.
        _should_reset = not getattr(self, "_skip_vllm_cleanup", False)
        if _should_reset:
            self._client = None
            self._client_base_url = None

        messages = self._build_messages(prompt, kwargs.get("system"))

        _prov_cfg = self._provider_cfg()
        token_param_name = _prov_cfg.get("token_param_name", "max_tokens")
        from utils.model_utils import resolve_token_budget

        raw_requested: int | None = kwargs.get("max_tokens")
        initial_tokens, _ = resolve_token_budget(
            model, raw_requested, self.config, kwargs.get("_module_key")
        )
        model_cfg_max_tokens = self._model_cfg(model).get("max_tokens")
        if model_cfg_max_tokens is not None:
            initial_tokens = min(initial_tokens, model_cfg_max_tokens)

        params: dict[str, Any] = {
            "model": self._server_model_name or model,
            "messages": messages,
            **self._resolve_sampling(model, temperature),
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
            return self._consume_stream(response_or_stream, stream_handler)

        return self._extract_response_content(response_or_stream, model)

    def _consume_stream(
        self,
        response_or_stream: Any,
        stream_handler: Callable[[str], None],
    ) -> str:
        """Streaming-Antwort konsumieren: Content an Handler, Metadata sammeln.

        Extrahiert aus :meth:`query` (DRY — senkt die Komplexität der
        Query-Methode unter das CC-12-Limit). Sammelt sichtbaren Content
        via ``stream_handler``, akkumuliert Reasoning via
        :class:`ThinkAccumulator` und wendet den gemeinsamen
        Reasoning-Fallback (:meth:`_apply_reasoning_fallback`) an.
        """
        full_content = ""
        from utils.providers.base import ThinkAccumulator

        think = ThinkAccumulator()
        for chunk in response_or_stream:
            if hasattr(chunk, "usage") and chunk.usage:
                self.last_response_metadata["usage"] = chunk.usage
            if chunk.choices:
                finish = getattr(chunk.choices[0], "finish_reason", None)
                if finish:
                    self.last_response_metadata["finish_reason"] = finish
                delta = chunk.choices[0].delta
                content_piece = getattr(delta, "content", None)
                if content_piece:
                    stream_handler(content_piece)
                    full_content += content_piece
                reasoning_piece = (
                    getattr(delta, "reasoning_content", None)
                    or getattr(delta, "reasoning", None)
                )
                if reasoning_piece:
                    think.add(reasoning_piece)

        if think.has_content:
            self.last_response_metadata["think_content"] = think.content
        usage = self.last_response_metadata.get("usage")
        if usage:
            self._apply_reasoning_fallback(usage, full_content, think.content)
        return full_content

    def _apply_reasoning_fallback(
        self,
        usage: Any,
        content: str,
        reasoning: str | None,
    ) -> None:
        """vLLM 0.25.1 reasoning_tokens-Heuristik als Shared-Helper (DRY).

        vLLM 0.22+ benennt ``reasoning_content`` -> ``reasoning`` um und befüllt
        ``completion_tokens_details.reasoning_tokens`` nicht zuverlässig. Diese
        Methode wendet die Base-Utilities (``_extract_reasoning_tokens`` ->
        ``_estimate_reasoning_tokens``) an und schreibt das Ergebnis nach
        ``last_response_metadata["reasoning_tokens"]``.

        Genutzt vom Streaming- und Non-Streaming-Pfad gemeinsam — keine
        Inline-Duplikation der Fallback-Logik mehr (siehe .agent/provider-models.md:
        „NIEMALS eigene Inline-Extraction schreiben").
        """
        rt = self._extract_reasoning_tokens(usage)
        if rt is None:
            completion_tokens = (
                getattr(usage, "completion_tokens", 0) if usage else 0
            )
            rt = self._estimate_reasoning_tokens(completion_tokens, content, reasoning)
        if rt is not None:
            self.last_response_metadata["reasoning_tokens"] = rt

    def get_available_models(self) -> list[str]:
        """Returns the list of models the server currently advertises via ``/v1/models``.

        Reihenfolge:
        1. Live-Liste vom laufenden vLLM-Server (``/v1/models``)
        2. Statische Config (``providers.local.<key>.models[].id``)
        3. Auto-Discovery der TOMLs im Remote-Verzeichnis (SoT)
        """
        try:
            resp = self.client.models.list()
            live = [m.id for m in resp.data]
            if live:
                return live
        except Exception as exc:
            logger.debug("Could not list vLLM models from server: %s", exc)

        static = [
            m.get("id", "")
            for m in self._provider_cfg().get("models", [])
            if m.get("id")
        ]
        if static:
            return static

        # Fallback: TOML-Auto-Discovery auf dem Remote-Host.
        return self._discover_remote_tomls()
