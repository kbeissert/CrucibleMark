"""
Cohere Provider Client
Native v2 API connector for Cohere Command models.
Endpoint: POST https://api.cohere.com/v2/chat

ToolUse-Modul: Verwendet Cohere-native `tools`-API statt Prompt-basierte JSON-Schemas.
Reasoning-Modelle (command-a-plus, command-a-reasoning) kollidieren mit prompt-basierten
Tool-Schemas → HTTP 422/500. Native tools umgeht das Problem vollständig.
"""

import json
import logging
from typing import Any
from collections.abc import Callable

import httpx

from utils.providers.base import BaseProviderClient

logger = logging.getLogger(__name__)

_COHERE_BASE_URL = "https://api.cohere.com/v2"

# Cohere models that auto-enable reasoning/thinking by default.
# Matched as substrings — "command-r-plus" will NOT match "command-a-plus".
_COHERE_REASONING_PREFIXES = ("command-a-reasoning", "command-a-plus")


def _is_cohere_reasoning_model(model: str) -> bool:
    """True if Cohere model supports reasoning (auto-thinking enabled by API)."""
    return any(tag in model for tag in _COHERE_REASONING_PREFIXES)


def _extract_tool_schema(system_prompt: str) -> dict[str, Any] | None:
    """Extract tool schema JSON from the ToolUse system prompt.

    The system prompt template contains the tool schema as a JSON object
    after 'Verfügbares Tool:\\n'. Uses bracket counting to handle nested JSON.
    Returns the parsed schema dict or None if not found.
    """
    if not system_prompt:
        return None
    marker = "Verfügbares Tool:\n"
    idx = system_prompt.find(marker)
    if idx < 0:
        return None
    json_start = idx + len(marker)
    # Bracket counting to find the matching closing brace
    depth = 0
    json_end = json_start
    for i, ch in enumerate(system_prompt[json_start:], json_start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                json_end = i + 1
                break
    if json_end <= json_start:
        return None
    try:
        return json.loads(system_prompt[json_start:json_end])
    except json.JSONDecodeError:
        logger.debug("Cohere: Failed to parse tool schema from system prompt")
        return None


def _schema_to_cohere_tools(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert a benchmark tool schema to Cohere native tools format.

    Input schema:
        {"name": "web_search", "description": "...", "parameters": {"query": {"type": "string", ...}}}
    Output:
        [{"type": "function", "function": {"name": "web_search", "description": "...", "parameters": {...}}}]
    """
    name = schema.get("name", "")
    description = schema.get("description", "")
    raw_params = schema.get("parameters", {})

    # Convert flat parameter dict to JSON Schema format
    properties: dict[str, Any] = {}
    required: list[str] = []
    for param_name, param_def in raw_params.items():
        prop: dict[str, Any] = {"type": param_def.get("type", "string")}
        if "description" in param_def:
            prop["description"] = param_def["description"]
        if "default" not in param_def:
            required.append(param_name)
        properties[param_name] = prop

    parameters: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        parameters["required"] = required

    return [{
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }]


def _format_tool_calls_as_text(tool_calls: list[dict[str, Any]]) -> str:
    """Format Cohere native tool_calls as JSON text matching benchmark expectations.

    The ToolUse benchmark parses responses expecting:
        {"tool_call": {"name": "...", "parameters": {...}}}

    Cohere returns:
        [{"type": "function", "function": {"name": "...", "arguments": "{...}"}}]
    """
    results: list[str] = []
    for tc in tool_calls:
        func = tc.get("function", {})
        name = func.get("name", "")
        raw_args = func.get("arguments", "{}")
        try:
            params = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError:
            params = {}
        results.append(json.dumps(
            {"tool_call": {"name": name, "parameters": params}},
            ensure_ascii=False,
        ))
    return "\n".join(results)


class CohereClient(BaseProviderClient):
    """Cohere Provider Client (native v2 REST API)."""

    PROVIDER_NAMES = ["cohere"]
    PROVIDER_CONFIG_KEY = "cohere"
    DEFAULT_TOKEN_PARAM = "max_tokens"

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._api_key: str | None = None
        self._http: httpx.Client | None = None

    @property
    def http(self) -> httpx.Client:
        """Lazy-loaded httpx client."""
        if self._http is None:
            api_key = self._get_api_key()
            self._http = httpx.Client(
                base_url=_COHERE_BASE_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "X-Client-Name": "cruciblemark",
                },
                timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0),
            )
        return self._http

    def _get_api_key(self) -> str:
        if self._api_key is None:
            import os
            self._api_key = os.environ.get("COHERE_API_KEY", "")
            if not self._api_key:
                raise ValueError("COHERE_API_KEY environment variable not set")
        return self._api_key

    def is_accessible(self) -> bool:
        """Prüft Zugang zur Cohere API."""
        try:
            resp = self.http.post("/chat", json={
                "stream": False,
                "model": "command-a-03-2025",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 1,
            })
            if resp.status_code == 200:
                return True
            if resp.status_code in (401, 403):
                logger.warning("Cohere Access Check: Auth fehlgeschlagen (HTTP %d)", resp.status_code)
                return False
            if resp.status_code == 429:
                logger.warning("Cohere Access Check: Rate Limit — API erreichbar")
                return True
            if resp.status_code == 404:
                logger.warning("Cohere Access Check: Testmodell nicht gefunden, API aber erreichbar")
                return True
            logger.debug("Cohere Access Check: HTTP %d — %s", resp.status_code, resp.text[:200])
            return False
        except Exception as e:
            logger.debug("Cohere Access Check Failed: %s", e)
            return False

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Callable[[str], None] | None = None,
        **kwargs,
    ) -> str:
        """Query Cohere v2 Chat API.

        For ToolUse module: uses Cohere native ``tools`` API instead of
        prompt-based JSON schemas. This avoids HTTP 422/500 errors that
        reasoning models exhibit with prompt-based tool calling.
        """
        try:
            _system = kwargs.get("system")
            _module_key = kwargs.get("_module_key")
            token_param_name, max_tokens = self._resolve_request_tokens(model, kwargs)

            messages = self._build_cohere_messages(prompt, _system)
            body: dict[str, Any] = {
                "stream": False,
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "seed": 42,
            }

            use_native_tools = False
            self._apply_cohere_thinking_config(body, model, _module_key, max_tokens)
            use_native_tools = self._apply_cohere_native_tools(body, model, _module_key, _system)

            logger.debug("Cohere request body keys: %s", list(body.keys()))
            resp = self.http.post("/chat", json=body)
            resp = self._handle_cohere_response_errors(resp, body, use_native_tools)

            if resp.status_code != 200:
                logger.error("Cohere API Error HTTP %d: %s", resp.status_code, resp.text[:500])
                resp.raise_for_status()

            data = resp.json()
            finish_reason = data.get("finish_reason", "")
            usage = data.get("usage", {})
            tokens = usage.get("tokens", {})
            msg = data.get("message", {})
            content_blocks = msg.get("content", [])
            tool_calls = msg.get("tool_calls", [])

            input_tokens = tokens.get("input_tokens", 0)
            output_tokens = tokens.get("output_tokens", 0)

            if tool_calls and use_native_tools:
                content = _format_tool_calls_as_text(tool_calls)
                self.last_response_metadata = {
                    "id": data.get("id"),
                    "model": model,
                    "finish_reason": finish_reason,
                    "token_limit_used": max_tokens,
                    "token_limit_fallback": False,
                    "usage": usage,
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "reasoning_tokens": tokens.get("reasoning_tokens"),
                }
                if stream_handler and content:
                    stream_handler(content)
                return content

            content, think_parts = self._collect_cohere_text_and_thinking(content_blocks)
            reasoning_token_count = tokens.get("reasoning_tokens") if think_parts else None

            self.last_response_metadata = {
                "id": data.get("id"),
                "model": model,
                "finish_reason": finish_reason,
                "token_limit_used": max_tokens,
                "token_limit_fallback": False,
                "usage": usage,
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "reasoning_tokens": reasoning_token_count,
            }
            if think_parts:
                self.last_response_metadata["think_content"] = "".join(think_parts)

            if stream_handler and content:
                stream_handler(content)

            return content

        except httpx.HTTPStatusError:
            raise
        except Exception as e:
            logger.error("Cohere query failed: %s", e)
            raise

    def _build_cohere_messages(self, prompt: str, system: str | None) -> list[dict]:
        """Baut die messages-Liste für die Cohere Chat API."""
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _apply_cohere_thinking_config(
        self,
        body: dict[str, Any],
        model: str,
        module_key: str | None,
        max_tokens: int,
    ) -> None:
        """Setzt thinking-Config für Reasoning-Modelle (Cohere)."""
        if not _is_cohere_reasoning_model(model):
            return
        if module_key == "tooluse":
            body["thinking"] = {"type": "disabled"}
            logger.debug("Cohere reasoning + tooluse: thinking disabled")
            return
        thinking_budget = max(max_tokens - 4000, 1000)
        body["thinking"] = {"type": "enabled", "token_budget": thinking_budget}
        logger.debug(
            "Cohere reasoning model: thinking.type=enabled, thinking.token_budget=%d",
            thinking_budget,
        )

    def _apply_cohere_native_tools(
        self,
        body: dict[str, Any],
        model: str,
        module_key: str | None,
        system: str | None,
    ) -> bool:
        """Fügt native tools für ToolUse-Modul hinzu, gibt use_native_tools zurück."""
        if module_key != "tooluse" or not system:
            return False
        tool_schema = _extract_tool_schema(system)
        if not tool_schema:
            return False
        body["tools"] = _schema_to_cohere_tools(tool_schema)
        logger.debug(
            "Cohere native tools: %s (reasoning=%s)",
            tool_schema.get("name"),
            _is_cohere_reasoning_model(model),
        )
        return True

    def _handle_cohere_response_errors(
        self,
        resp: httpx.Response,
        body: dict[str, Any],
        use_native_tools: bool,
    ) -> httpx.Response:
        """Behandelt Rate-Limit (429 → Raise) und native-tool 500 → Retry."""
        if resp.status_code == 429:
            retry_after = resp.headers.get("retry-after")
            wait = int(retry_after) if retry_after else 60
            logger.warning("Cohere Rate Limit (429). Retry-After: %ds", wait)
            raise httpx.HTTPStatusError(
                f"429 Too Many Requests (retry_after={wait}s)",
                request=resp.request,
                response=resp,
            )

        if resp.status_code == 500 and use_native_tools:
            import time as _time
            for _retry_i in range(2):
                wait = 2 * (_retry_i + 1)
                logger.warning("Cohere 500 with native tools — retry %d/2 (wait %ds)", _retry_i + 1, wait)
                _time.sleep(wait)
                resp = self.http.post("/chat", json=body)
                if resp.status_code != 500:
                    break
        return resp

    def _collect_cohere_text_and_thinking(
        self, content_blocks: list[dict[str, Any]],
    ) -> tuple[str, list[str]]:
        """Sammelt Text- und Thinking-Bausteine aus Cohere-Content-Blöcken."""
        text_parts: list[str] = []
        think_parts: list[str] = []
        for block in content_blocks:
            block_type = block.get("type", "")
            if block_type == "text":
                text_parts.append(block.get("text", ""))
            elif block_type == "thinking":
                think_parts.append(block.get("thinking", ""))
        return "".join(text_parts), think_parts

    def _extract_reasoning_tokens(self, usage: Any) -> int | None:
        """Genuine Cohere-spezifische Override (KEIN dead stub).

        Cohere nutzt ein abweichendes Usage-Format:
        ``{tokens: {input_tokens, output_tokens, reasoning_tokens}}``.
        Die Base-Methode in ``base.py`` prueft OpenAI/Anthropic/Mistral-Pfade,
        die bei Cohere nicht zutreffen. Daher ist diese Override noetig.

        Siehe auch: ``tests/test_provider_reasoning_ssot.py`` (Guardrail-Test
        der sicherstellt, dass nur ``cohere.py`` eine Override definiert).
        """
        if isinstance(usage, dict):
            tokens = usage.get("tokens", {})
            return tokens.get("reasoning_tokens")
        return None

    def get_available_models(self) -> list[str]:
        return [
            "command-a-plus-05-2026",
            "command-a-03-2025",
            "command-a-reasoning-08-2025",
            "command-a-vision-07-2025",
            "command-r7b-12-2024",
            "command-r-plus-08-2024",
            "command-r-08-2024",
        ]
