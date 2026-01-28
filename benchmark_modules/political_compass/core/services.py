# benchmark_modules/political_compass/services.py
"""
LLM Services Module
===================

Handles communication with external LLM providers (Ollama, OpenAI, Anthropic).
Encapsulates logic for retries, rate limiting, and unified API.
"""

import os
import time
import logging
import random
from typing import Optional, Any

import requests

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore

from .models import Question
from .config import LLM_CONFIGS


class MockLLMService:
    """
    Zentrale Mock-Implementierung für alle Tests.
    Simuliert Antworten für Dry-Runs und Tests ohne echte LLM-Kosten.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, provider: str = "mock", model: str = "random"):
        self.provider = provider
        self.model = model

    def query(self, _question: Question) -> str:
        """Simuliert eine Antwort basierend auf Standard-Mustern."""
        options = ["A", "B", "C", "D"]
        formats = [
            lambda x: f"Ich wähle {x}.",
            lambda x: f"Answer: {x}",
            lambda x: x,
            lambda x: f"Option {x} ist am besten."
        ]
        chosen = random.choice(options)
        fmt = random.choice(formats)
        return fmt(chosen)

    def query_raw(self, prompt: str, request_id: str = "unknown", system_prompt: str | None = None) -> str:
        """Mock raw query."""
        _ = (prompt, request_id, system_prompt) # Unused
        return self.query(Question("", "", "", "", "", "", {}))


class FrameworkAdapter:
    """Adaptiert den generischen CrucibleMark Client auf das Module-Interface."""
    # pylint: disable=too-few-public-methods

    def __init__(self, client: Any, provider: str, model: str):
        self.client = client
        self.provider = provider
        self.model = model
        self.default_temperature = 0.0

    def query(self, question: Question) -> Optional[str]:
        """Sendet Query über den adaptierten Client."""
        # FrameworkAdapter nutzt in der Regel Standard-Settings
        prompt = question.to_prompt()
        return self.query_prompt(prompt)

    def query_prompt(self, prompt: str) -> Optional[str]:
        """Helper to send raw prompt via client."""
        try:
            return self.client.query(
                model=self.model,
                prompt=prompt,
                provider=self.provider,
                temperature=self.default_temperature,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.error("FrameworkAdapter Error: %s", e)
            return None


class LLMInterface:
    """
    Interface für verschiedene LLM-Provider (Ollama, OpenAI, Anthropic).
    Implementiert Retry-Logik, Rate-Limiting und einheitliches Prompting.
    """

    def __init__(self, provider: str, model: str, **kwargs):
        """
        Initialisiert das Interface.

        Args:
            provider: 'ollama', 'openai', oder 'anthropic'
            model: Modellname (z.B. 'qwen2.5:14b', 'gpt-4o')
            kwargs: Überschreibt Config (z.B. temperature=0.7, api_key=...)
        """
        self.provider = provider.lower()
        self.model = model
        self.config = LLM_CONFIGS.get(self.provider, {}).copy()

        # Merge kwargs into config
        self.config.update(kwargs)
        self.rate_limit_delay = self.config.get("rate_limit_delay", 1.0)
        passed_api_key = self.config.get("api_key")

        # Client Typisierung für Mypy
        self.client: Any = None

        # Clients initialisieren (Lazy Loading der Libraries)
        if self.provider == "openai":
            if OpenAI is None:
                raise ImportError("OpenAI module not installed.")
            try:
                api_key = passed_api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logging.warning("⚠️  WARNUNG: OPENAI_API_KEY nicht gesetzt.")
                self.client = OpenAI(api_key=api_key)
            except ImportError:
                logging.error("❌ OpenAI Library nicht installiert. `pip install openai`")

        elif self.provider == "anthropic":
            if Anthropic is None:
                raise ImportError("Anthropic module not installed.")
            try:
                api_key = passed_api_key or os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    logging.warning("⚠️  WARNUNG: ANTHROPIC_API_KEY nicht gesetzt.")
                self.client = Anthropic(api_key=api_key)
            except ImportError:
                logging.error("❌ Anthropic Library nicht installiert. `pip install anthropic`")

    def query(self, question: Question) -> Optional[str]:
        """Sendet Frage an LLM und gibt rohe Antwort zurück."""
        prompt = question.to_prompt()
        return self.query_raw(prompt, str(question.id))

    def query_raw(self, prompt: str, request_id: str = "unknown", system_prompt: str | None = None) -> Optional[str]:
        """Sendet rohen Prompt an LLM mit Retry-Logik."""
        return self._query_with_retry(prompt, request_id, system_prompt=system_prompt)

    def _query_with_retry(
        self, prompt: str, request_id: str, max_retries: int = 3, system_prompt: str | None = None
    ) -> Optional[str]:
        """Führt LLM-Request mit Retry und Rate-Limiting aus."""

        for attempt in range(max_retries):
            try:
                logging.info(
                    "REQUEST (%s/%s) - ID: %s", self.provider, self.model, request_id
                )

                response = None
                if self.provider == "ollama":
                    response = self._call_ollama(prompt, system_prompt)
                elif self.provider == "openai":
                    response = self._call_openai(prompt, system_prompt)
                elif self.provider == "anthropic":
                    response = self._call_anthropic(prompt, system_prompt)
                else:
                    logging.error("❌ Unbekannter Provider: %s", self.provider)
                    return None

                # Falls Response None ist, Exception werfen
                if response is None:
                    raise ValueError("Empty response received")

                logging.info(
                    "RESPONSE (%s/%s) - ID: %s: %s...",
                    self.provider,
                    self.model,
                    request_id,
                    response[:100] if response else "",
                )

                # Rate Limiting Sleep
                time.sleep(self.rate_limit_delay)
                return response

            except Exception as e:  # pylint: disable=broad-exception-caught
                wait_time = 2**attempt
                logging.warning("  ⚠️  Fehler (Versuch %d/%d): %s", attempt + 1, max_retries, e)
                logging.error(
                    "ERROR (%s/%s) - ID: %s: %s",
                    self.provider,
                    self.model,
                    request_id,
                    e,
                )

                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    logging.error("  ❌ Max retries erreicht.")
        return None

    def _call_ollama(self, prompt: str, system_prompt: str | None = None) -> str:
        url = self.config["endpoint"]
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.get(
                    "temperature", self.config["default_temperature"]
                )
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        resp = requests.post(url, json=payload, timeout=self.config["timeout"])
        resp.raise_for_status()
        return resp.json()["response"]

    def _call_openai(self, prompt: str, system_prompt: str | None = None) -> str:
        sys_msg = system_prompt if system_prompt else "Du bist ein neutraler Beobachter."

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt},
            ],
            temperature=self.config.get(
                "temperature", self.config["default_temperature"]
            ),
            max_tokens=self.config["max_tokens"],
        )
        return response.choices[0].message.content or ""

    def _call_anthropic(self, prompt: str, system_prompt: str | None = None) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": self.config["max_tokens"],
            "temperature": self.config.get(
                "temperature", self.config["default_temperature"]
            ),
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        return response.content[0].text
