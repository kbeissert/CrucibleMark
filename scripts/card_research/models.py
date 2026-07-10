from __future__ import annotations

import logging
import time
from dataclasses import field
from pathlib import Path
from typing import Any

import httpx
import openai
from openai import OpenAI

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0
PER_CALL_TIMEOUT_S = 60

class CardFinding:
    field: str
    severity: str
    message: str
    current: Any = None
    suggested: Any = None


class CardCheckReport:
    model_id: str
    card_path: Path
    findings: list[CardFinding] = field(default_factory=list)
    summary: str = ""
    raw_response: str = ""
    parse_error: str | None = None
    error: str | None = None
    would_write: bool = False


class CardMakeReport:
    model_id: str
    card_path: Path
    new_card: dict = field(default_factory=dict)
    raw_response: str = ""
    parse_error: str | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
    would_write: bool = False
    wrote: bool = False


class RunSummary:
    processed: int = 0
    skipped: int = 0
    errors: int = 0
    check_reports: list[CardCheckReport] = field(default_factory=list)
    make_reports: list[CardMakeReport] = field(default_factory=list)
    research_reports: list[ResearchReport] = field(default_factory=list)


class ResearchReport:
    model_id: str
    card_path: Path
    findings: list[CardFinding] = field(default_factory=list)
    summary: str = ""
    raw_response: str = ""
    parse_error: str | None = None
    error: str | None = None
    locked: bool = False
    unlocked: bool = False
    would_write: bool = False
    wrote: bool = False
    profile_verified: bool = False
    backup_path: Path | None = None


class LLMSpec:
    provider_name: str
    model: str
    base_url: str
    api_key: str | None
    max_tokens: int
    temperature: float


logger = logging.getLogger("manage_model_cards")

class LLMSession:
    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str | None,
        max_retries: int,
        timeout_s: int,
    ) -> None:
        self.model = model
        self.max_retries = max_retries
        self.timeout_s = timeout_s
        kwargs: dict[str, Any] = {}
        if base_url:
            kwargs["base_url"] = base_url
        if api_key:
            kwargs["api_key"] = api_key
        self._client = OpenAI(**kwargs)

    def query(self, system: str, user: str, temperature: float) -> str:
        last_exc: Exception | None = None
        timeout = httpx.Timeout(timeout=self.timeout_s, connect=10.0, read=self.timeout_s, pool=self.timeout_s)
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=temperature,
                    timeout=timeout,
                )
                content = response.choices[0].message.content or ""
                return content
            except openai.APIError as exc:  # noqa: BLE001 — wir retryen alle API-Fehler
                last_exc = exc
                if attempt >= self.max_retries:
                    break
                backoff = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "LLM-Aufruf fehlgeschlagen (Versuch %d/%d): %s — retry in %.1fs",
                    attempt, self.max_retries, exc, backoff,
                )
                time.sleep(backoff)
        assert last_exc is not None
        raise last_exc

