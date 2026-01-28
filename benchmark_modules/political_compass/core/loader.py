import yaml
from pathlib import Path
from typing import List, Optional
from benchmark_modules.political_compass.core.models import Question

class QuestionLoader:
    """Helper class to load and parse Question objects from YAML files."""

    @staticmethod
    def _parse_yaml_content(content: str, source_name: str = "unknown") -> list[Question]:
        """Parses YAML content and extracts Question objects."""
        questions: list[Question] = []
        documents = content.split("---")
        for doc in documents:
            if not doc.strip() or doc.strip().startswith("#"):
                continue

            cleaned_doc = "\n".join(
                [line for line in doc.splitlines() if not line.strip().startswith("==")]
            )

            try:
                data = yaml.safe_load(cleaned_doc)
                if not data or "metadata" not in data:
                    continue

                question = Question(
                    id=data["metadata"]["id"],
                    module=data["metadata"]["module"],
                    axis=data["metadata"]["axis"],
                    topic=data["metadata"]["topic"],
                    context=data.get("context", data.get("slogan", "")),
                    question=data["question"],
                    options=data["options"],
                    extremism_warning=data["metadata"].get("extremism_warning", False),
                )
                questions.append(question)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Fehler beim Laden von Frage aus {source_name}: {e}")
        
        return questions

    @classmethod
    def load_from_path(cls, path: Path) -> list[Question]:
        """Loads questions from a single YAML file."""
        if not path.exists():
            return []
            
        with open(path, encoding="utf-8") as f:
            return cls._parse_yaml_content(f.read(), source_name=path.name)

    @classmethod
    def load_from_directory(cls, directory: Path) -> list[Question]:
        """Loads questions from all YAML files in a directory."""
        if not directory.exists():
            print(f"Keine Assets gefunden in {directory}")
            return []

        files = sorted(directory.glob("*.yaml"))
        if not files:
            return []

        print(f"Lade Fragen aus {len(files)} Dateien...")
        
        all_questions = []
        for file_path in files:
            questions = cls.load_from_path(file_path)
            all_questions.extend(questions)
            
        print(f"Gesamt: {len(all_questions)} Fragen geladen.")
        return all_questions
