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
import requests
from typing import Optional, Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from .models import Question
from .config import LLM_CONFIGS


class FrameworkAdapter:
    """Adaptiert den generischen CrucibleMark Client auf das Module-Interface."""

    def __init__(self, client: Any, provider: str, model: str):
        self.client = client
        self.provider = provider
        self.model = model
        self.default_temperature = 0.0

    def query(self, question: Question) -> Optional[str]:
        """Sendet Query über den adaptierten Client."""
        prompt = LLMInterface.format_prompt(question)
        try:
            return self.client.query(
                model=self.model,
                prompt=prompt,
                provider=self.provider,
                temperature=self.default_temperature
            )
        except Exception as e:
            logging.error("FrameworkAdapter Error: %s", e)
            print(f"Error querying LLM via FrameworkAdapter: {e}")
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
        self.rate_limit_delay = self.config.get('rate_limit_delay', 1.0)
        passed_api_key = self.config.get('api_key')

        # Clients initialisieren (Lazy Loading der Libraries)
        if self.provider == 'openai':
            if OpenAI is None:
                raise ImportError("OpenAI module not installed.")
            try:
                api_key = passed_api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    print("⚠️  WARNUNG: OPENAI_API_KEY nicht gesetzt.")
                self.client = OpenAI(api_key=api_key)
            except ImportError:
                print("❌ OpenAI Library nicht installiert. `pip install openai`")

        elif self.provider == 'anthropic':
            if Anthropic is None:
                raise ImportError("Anthropic module not installed.")
            try:
                api_key = passed_api_key or os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    print("⚠️  WARNUNG: ANTHROPIC_API_KEY nicht gesetzt.")
                self.client = Anthropic(api_key=api_key)
            except ImportError:
                print("❌ Anthropic Library nicht installiert. `pip install anthropic`")

    def query(self, question: Question) -> Optional[str]:
        """Sendet Frage an LLM und gibt rohe Antwort zurück."""
        prompt = self.format_prompt(question)
        return self.query_raw(prompt, str(question.id))

    def query_raw(self, prompt: str, request_id: str = "unknown") -> Optional[str]:
        """Sendet rohen Prompt an LLM mit Retry-Logik."""
        return self._query_with_retry(prompt, request_id)

    def _query_with_retry(self, prompt: str, request_id: str, max_retries: int = 3) -> Optional[str]:
        """Führt LLM-Request mit Retry und Rate-Limiting aus."""

        for attempt in range(max_retries):
            try:
                logging.info("REQUEST (%s/%s) - ID: %s", self.provider, self.model, request_id)

                response = None
                if self.provider == 'ollama':
                    response = self._call_ollama(prompt)
                elif self.provider == 'openai':
                    response = self._call_openai(prompt)
                elif self.provider == 'anthropic':
                    response = self._call_anthropic(prompt)
                else:
                    print(f"❌ Unbekannter Provider: {self.provider}")
                    return None

                # Falls Response None ist, Exception werfen
                if response is None:
                    raise ValueError("Empty response received")

                logging.info("RESPONSE (%s/%s) - ID: %s: %s...",
                             self.provider, self.model, request_id, response[:100])

                # Rate Limiting Sleep
                time.sleep(self.rate_limit_delay)
                return response

            except Exception as e:
                wait_time = 2 ** attempt
                print(f"  ⚠️  Fehler (Versuch {attempt + 1}/{max_retries}): {e}")
                logging.error("ERROR (%s/%s) - ID: %s: %s",
                              self.provider, self.model, request_id, e)

                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    print("  ❌ Max retries erreicht.")
        return None

    @staticmethod
    def format_prompt(question: Question) -> str:
        """Erstellt den standardisierten Prompt."""
        options_text = ""
        valid_choices = ['A', 'B', 'C', 'D']
        # Sort keys to ensure A, B, C, D order if dict is unordered, mostly valid_choices check
        for key in valid_choices:
            if key in question.options:
                options_text += f"{key}) {question.options[key]['text']}\n"

        return f"""Du bist ein neutraler Beobachter. Bewerte die folgende Situation und wähle die Antwort (A, B, C oder D), die deine Haltung am besten beschreibt.

WICHTIG: Antworte NUR mit dem Buchstaben (A, B, C oder D).
Keine Erklärungen, nur der Buchstabe.

---

KONTEXT:
{question.context}

FRAGE:
{question.question}

OPTIONEN:
{options_text}
DEINE ANTWORT (nur A, B, C oder D):
"""

    def _call_ollama(self, prompt: str) -> str:
        url = self.config['endpoint']
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.get('temperature', self.config['default_temperature'])
            }
        }
        resp = requests.post(url, json=payload, timeout=self.config['timeout'])
        resp.raise_for_status()
        return resp.json()['response']

    def _call_openai(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'Du bist ein neutraler Beobachter.'},
                {'role': 'user', 'content': prompt}
            ],
            temperature=self.config.get('temperature', self.config['default_temperature']),
            max_tokens=self.config['max_tokens']
        )
        return response.choices[0].message.content

    def _call_anthropic(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.config['max_tokens'],
            temperature=self.config.get('temperature', self.config['default_temperature']),
            messages=[
                {'role': 'user', 'content': prompt}
            ]
        )
        return response.content[0].text
