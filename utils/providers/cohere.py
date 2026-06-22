"""
Cohere Provider Client
Native v2 API connector for Cohere Command models.
Endpoint: POST https://api.cohere.com/v2/chat
"""

import json
import logging
from typing import Any, List, Optional, Callable

import httpx

from utils.providers.base import BaseProviderClient

logger = logging.getLogger(__name__)

_COHERE_BASE_URL = "https://api.cohere.com/v2"


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
                "model": "command-a-plus-05-2026",
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
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """Query Cohere v2 Chat API."""
        try:
            _system = kwargs.get("system")
            token_param_name, max_tokens = self._resolve_request_tokens(model, kwargs)

            messages: list[dict] = []
            if _system:
                messages.append({"role": "system", "content": _system})
            messages.append({"role": "user", "content": prompt})

            body: dict[str, Any] = {
                "stream": False,
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "seed": 42,
            }

            if "reasoning" in model:
                thinking_budget = max(max_tokens - 4000, 1000)
                body["thinking"] = {"token_budget": thinking_budget}
                logger.debug(
                    "Cohere reasoning model: thinking.token_budget=%d, max_tokens=%d",
                    thinking_budget, max_tokens,
                )

            logger.debug("Cohere request body: %s", json.dumps(body, default=str)[:500])
            resp = self.http.post("/chat", json=body)

            if resp.status_code == 429:
                retry_after = resp.headers.get("retry-after")
                wait = int(retry_after) if retry_after else 60
                logger.warning("Cohere Rate Limit (429). Retry-After: %ds", wait)
                raise httpx.HTTPStatusError(
                    f"429 Too Many Requests (retry_after={wait}s)",
                    request=resp.request,
                    response=resp,
                )

            if resp.status_code != 200:
                logger.error("Cohere API Error HTTP %d: %s", resp.status_code, resp.text[:500])
                resp.raise_for_status()

            data = resp.json()
            finish_reason = data.get("finish_reason", "")
            usage = data.get("usage", {})
            tokens = usage.get("tokens", {})

            content_blocks = data.get("message", {}).get("content", [])
            text_parts: list[str] = []
            think_parts: list[str] = []
            for block in content_blocks:
                block_type = block.get("type", "")
                if block_type == "text":
                    text_parts.append(block.get("text", ""))
                elif block_type == "thinking":
                    think_parts.append(block.get("thinking", ""))

            content = "".join(text_parts)

            input_tokens = tokens.get("input_tokens", 0)
            output_tokens = tokens.get("output_tokens", 0)
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
                "reasoning_tokens": reasoning_token_count if think_parts else None,
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

    def _extract_reasoning_tokens(self, usage: Any) -> int | None:
        """Cohere usage format: {tokens: {input_tokens, output_tokens}}.
        Kein separates reasoning_tokens Feld — wird aus think_content abgeleitet.
        """
        return None

    def get_available_models(self) -> List[str]:
        return [
            "command-a-plus-05-2026",
            "command-a-03-2025",
            "command-a-reasoning-08-2025",
            "command-a-vision-07-2025",
            "command-r7b-12-2024",
            "command-r-plus-08-2024",
            "command-r-08-2024",
        ]
