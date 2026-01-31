"""Loader-Modul für YAML-basierte Fragen im Political Compass Benchmark."""


import logging
from pathlib import Path
from typing import Any

import yaml
from yaml import YAMLError

from benchmark_modules.political_compass.core.models import Question

from .constants import DEFAULT_ENCODING

logger = logging.getLogger(__name__)


class QuestionLoader:
    """Helper class to load and parse Question objects from YAML files."""

    @staticmethod
    def _validate_data(
        data: dict[str, Any], doc_index: int, source_name: str,
    ) -> Question | None:
        """Validierte Extraktion eines Question-Objekts."""
        try:
            # Metadata Check
            if not data or "metadata" not in data:
                # Leere Dokumente oder Header ignorieren wir stillschweigend
                # oder mit Debug-Log
                if data:
                    logger.debug(
                        "Dokument #%d in %s hat keine Metadaten.",
                        doc_index,
                        source_name,
                    )
                return None

            meta = data["metadata"]

            # Explizite Extraktion für bessere Lesbarkeit
            return Question(
                id=meta["id"],
                module=meta["module"],
                axis=meta["axis"],
                topic=meta["topic"],
                context=data.get("context", data.get("slogan", "")),
                question=data["question"],
                options=data["options"],
                extremism_warning=meta.get("extremism_warning", False),
            )
        except KeyError as e:
            logger.warning(
                "Fehlendes Pflichtfeld in %s (Doc #%d): %s", source_name, doc_index, e,
            )
            return None

    @classmethod
    def _parse_yaml_content(
        cls,
        content: str,
        source_name: str = "unknown",
    ) -> list[Question]:
        """Parse YAML content using Standard Parser."""
        questions: list[Question] = []

        try:
            # Standard Multi-Document Parser nutzen
            # Dies behandelt '---' korrekt und ignoriert Kommentare sicher.
            documents = yaml.safe_load_all(content)

            for i, data in enumerate(documents):
                question = cls._validate_data(data, i, source_name)
                if question:
                    questions.append(question)

        except YAMLError:
            logger.exception("YAML Syntax-Fehler in %s", source_name)
            return []

        return questions

    @classmethod
    def load_from_path(cls, path: Path) -> list[Question]:
        """Load questions from a single YAML file."""
        if not path.exists():
            logger.warning("Datei nicht gefunden: %s", path)
            return []

        try:
            with path.open(encoding=DEFAULT_ENCODING) as f:
                return cls._parse_yaml_content(f.read(), source_name=path.name)
        except OSError:
            logger.exception("Konnte Datei %s nicht lesen", path)
            return []

    @classmethod
    def load_from_directory(cls, directory: Path) -> list[Question]:
        """Load questions from all YAML files in a directory."""
        if not directory.exists():
            logger.warning("Keine Assets gefunden in %s", directory)
            return []

        files = sorted(directory.glob("*.yaml"))
        if not files:
            return []

        logger.info("Lade Fragen aus %d Dateien...", len(files))

        all_questions = []
        for file_path in files:
            questions = cls.load_from_path(file_path)
            all_questions.extend(questions)

        logger.info("Gesamt: %d Fragen geladen.", len(all_questions))
        return all_questions
