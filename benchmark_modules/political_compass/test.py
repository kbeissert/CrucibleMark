#!/usr/bin/env python3
"""
Political Compass Test - Core Module v3.0
==========================================

Testet LLMs auf politischen Bias anhand von 74 Fragen über 9 Themenmodule.
Integrierte Shuffling-Logik und v3.0 Scoring-Algorithmus.
"""

import json
import random
import re
import os
import time
import statistics
import logging
import argparse
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime

import yaml

from benchmark_modules.base_test import BaseTest
from utils.benchmark_ui import TerminalUI
from benchmark_modules.political_compass.core.config import (
    TOPIC_NAMES,
)
from benchmark_modules.political_compass.core.models import Question
from benchmark_modules.political_compass.core.evaluators import ArchetypeClassifier, ExtremismWatchdog
from benchmark_modules.political_compass.core.services import LLMInterface, FrameworkAdapter, MockLLMService
from benchmark_modules.political_compass.core.io_manager import ResultManager

# Setup basic logging
logging.basicConfig(
    filename="llm_requests.log", level=logging.INFO, format="%(asctime)s - %(message)s"
)


class PoliticalCompassTest(BaseTest):
    """
    Hauptklasse für Political Compass Tests.
    Inherits from BaseTest for integration into CrucibleMark.
    """

    def __init__(self, asset_path: Path | None = None):
        """
        Initialisiert Test.
        Args:
            asset_path: Pfad zum YAML-Asset (optional für Batch-Modus)
        """
        self.watchdog = ExtremismWatchdog()
        self.responses: List[dict] = []
        self.questions: List[Question] = []
        self.last_score_result: Dict[str, Any] = {}

        # Configuration
        self.num_runs = 3  # Default v3.0 requirement

        if asset_path:
            super().__init__(asset_path)
            self._load_questions_from_asset()
        else:
            # Standalone/Batch mode initialization
            self.asset_path = None  # type: ignore
            self.asset = {}

    def _parse_yaml_content(self, content: str, source_name: str = "unknown"):
        """Parst YAML Content und extrahiert Fragen."""
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
                self.questions.append(question)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Fehler beim Laden von Frage aus {source_name}: {e}")

    def load_questions(self, directory: str = "assets") -> int:
        """Lädt alle Fragen aus dem assets-Verzeichnis (für Batch-Modus)."""
        # Pfad-Auflösung: Zuerst relativ zum Modul, Fallback auf direkten Pfad (CWD/Absolut)
        base_path = Path(__file__).parent / directory
        if not base_path.exists():
            direct_path = Path(directory)
            if direct_path.exists():
                base_path = direct_path

        files = sorted(base_path.glob("*.yaml"))

        if not files:
            print(f"Keine Assets gefunden in {base_path}")
            return 0

        print(f"Lade Fragen aus {len(files)} Dateien...")

        self.questions = []
        for file_path in files:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            self._parse_yaml_content(content, source_name=file_path.name)

        print(f"Gesamt: {len(self.questions)} Fragen geladen.")
        return len(self.questions)

    def _validate_asset(self) -> None:
        """
        Validation override for Political Compass.
        BaseTest validiert auf 'prompt', was wir hier nicht haben (Multi-Question).
        """
        if "metadata" not in self.asset:
            raise ValueError("Asset missing metadata")

        required_meta = ["id", "module", "topic"]
        for field in required_meta:
            if field not in self.asset["metadata"]:
                raise ValueError(f"Asset metadata missing required field: {field}")

    def _load_questions_from_asset(self):
        """Läd Fragen aus dem aktuellen Asset-File."""
        with open(self.asset_path, encoding="utf-8") as f:
            content = f.read()

        self._parse_yaml_content(content, source_name=str(self.asset_path))

    def _construct_shuffled_prompt(
        self, question: Question, seed: int
    ) -> Tuple[str, Dict[str, str]]:
        """
        Erstellt Prompt mit randomisierten Antwortmöglichkeiten.
        Verhindert Position Bias (Tendenz immer 'A' zu wählen).
        
        Returns:
            Tuple[sys_prompt + user_prompt, mapping]
            Mapping: User Choice -> Original Choice (z.B. {'A': 'C'})
        """
        valid_keys = ["A", "B", "C", "D"]
        available_keys = [k for k in valid_keys if k in question.options]

        # Randomize order
        shuffled_keys = list(available_keys)
        rng = random.Random(seed)
        rng.shuffle(shuffled_keys)

        mapping = {}
        options_text = ""

        # i: index 0..3 (Displayed as A..D)
        # key: original logical key (A..D from yaml)
        for i, displayed_key in enumerate(available_keys):
            original_key = shuffled_keys[i]
            mapping[displayed_key] = original_key

            text = question.options[original_key]["text"]
            options_text += f"{displayed_key}) {text}\n"

        prompt = (
            f"KONTEXT:\n{question.context}\n\n"
            f"FRAGE:\n{question.question}\n\n"
            f"OPTIONEN:\n{options_text}\n\n"
            "DEINE ANTWORT (nur A, B, C oder D):"
        )
        return prompt, mapping

    def execute(
        self, model: str, llm_client: Any, provider: str = "ollama"
    ) -> Dict[str, Any]:
        """
        Ausführungsmethode für BenchmarkRunner.
        """
        start_time = time.time()

        # Init specific UI for this module
        ui = TerminalUI()

        intro_info = [
            "⚠️  WICHTIG: Dieser Benchmark führt 3 Runs durch.",
            "",
            "GRUND: Reduktion von Ausreißern & Bias (Mittelwert)",
            "",
            "🕐 Geschätzte Dauer: flexibel (abhängig vom Modell)"
        ]
        ui.print_intro(
            module_name="Political Compass",
            model_name=model,
            provider=provider,
            num_runs=self.num_runs,
            extra_info=intro_info
        )
        print(f"   Fragen geladen: {len(self.questions)}\n")

        # Use shared adapter
        adapter = FrameworkAdapter(llm_client, provider, model)

        self.responses = []

        # Sort questions by ID just in case
        self.questions.sort(key=lambda q: q.id)

        total_tokens_all_runs = 0
        total_cost_all_runs = 0.0

        # Track detailed stats per module across all runs
        # Format: "7.1": {"tokens": 0, "count": 0}
        self.final_module_stats = {}

        for i in range(self.num_runs):
            ui.start_run(i + 1, self.num_runs, model, provider)

            # Seed based on run index for reproducible shuffling
            run_seed = int(time.time()) + i

            run_start_idx = len(self.responses)
            current_block_id = None
            block_stats = {"count": 0, "total": 0, "cost": 0.0, "tokens": 0, "start_time": time.time()}

            # Pre-calc totals per block for this run
            block_totals = {}
            for q in self.questions:
                parts = q.id.split('_')
                code_parts = parts[-1].split('.')
                block_id = f"{code_parts[0]}.{code_parts[1]}" if len(code_parts) >= 2 else "7.0"
                block_totals[block_id] = block_totals.get(block_id, 0) + 1

            for q_idx, question in enumerate(self.questions):
                parts = question.id.split('_')
                code_parts = parts[-1].split('.')
                if len(code_parts) >= 2:
                    block_id = f"{code_parts[0]}.{code_parts[1]}"
                else:
                    block_id = "7.0"

                # Check Block Change
                if block_id != current_block_id:
                    # Previous block finished?
                    if current_block_id is not None:
                        elapsed_block = time.time() - block_stats["start_time"]
                        full_name = f"{current_block_id}_{TOPIC_NAMES.get(current_block_id, '').replace(' ', '_').lower()}"
                        ui.finish_block(full_name, elapsed_block, block_stats["tokens"], block_stats["cost"])

                        # Aggregation for Final Report
                        if current_block_id not in self.final_module_stats:
                            self.final_module_stats[current_block_id] = {"tokens": 0, "count": 0}
                        self.final_module_stats[current_block_id]["tokens"] += block_stats["tokens"]
                        self.final_module_stats[current_block_id]["count"] += block_stats["count"]

                    # Start New Block
                    topic_name = TOPIC_NAMES.get(block_id, "Unbekanntes Thema")
                    count_in_block = block_totals.get(block_id, 0)
                    ui.start_block(block_id, topic_name, count_in_block)
                    current_block_id = block_id
                    block_stats = {"count": 0, "total": count_in_block, "cost": 0.0, "tokens": 0, "start_time": time.time()}

                # Shuffling Logic per Question
                seed = run_seed + hash(question.id)
                prompt_text, mapping = self._construct_shuffled_prompt(question, seed)

                # Query Adapter
                try:
                    raw_resp = adapter.client.query(
                        model=model,
                        prompt=prompt_text,
                        provider=provider,
                        temperature=0.1
                    )

                    # Track Stats
                    if hasattr(adapter.client, 'last_request_cost'):
                         cost = adapter.client.last_request_cost or 0.0
                         block_stats["cost"] += cost
                         total_cost_all_runs += cost
                    if hasattr(adapter.client, 'last_token_usage'):
                         usage = adapter.client.last_token_usage or 0
                         block_stats["tokens"] += usage
                         total_tokens_all_runs += usage

                except Exception: # pylint: disable=broad-exception-caught
                    raw_resp = None

                block_stats["count"] += 1

                # Progress Line
                ui.update_progress(block_stats["count"], block_stats["total"], block_stats["tokens"], block_stats["cost"], finished=False)

                if raw_resp:
                    # Evaluate with mapping
                    result = self.evaluate_response(question, raw_resp, mapping)
                    self.responses.append(result)

            # End of Run Loop - Close Last Block
            if current_block_id is not None:
                 ui.update_progress(block_stats["count"], block_stats["total"], block_stats["tokens"], block_stats["cost"], finished=True)
                 elapsed_block = time.time() - block_stats["start_time"]
                 full_name = f"{current_block_id}_{TOPIC_NAMES.get(current_block_id, '').replace(' ', '_').lower()}"
                 ui.finish_block(full_name, elapsed_block, block_stats["tokens"], block_stats["cost"])

                 # Aggregation for Final Report (Last Block)
                 if current_block_id not in self.final_module_stats:
                     self.final_module_stats[current_block_id] = {"tokens": 0, "count": 0}
                 self.final_module_stats[current_block_id]["tokens"] += block_stats["tokens"]
                 self.final_module_stats[current_block_id]["count"] += block_stats["count"]

            # --- Run Summary ---
            run_resps = self.responses[run_start_idx:]
            if run_resps:
                run_coords = ArchetypeClassifier.calculate_scores_v2(run_resps)
                debug_data = run_coords.get("debug", {})
                x_mean = round(debug_data.get("x_mean", 0), 2)
                y_mean = round(debug_data.get("y_mean", 0), 2)
                x_bonus = round(run_coords["x"] - x_mean, 2)
                y_bonus = round(run_coords["y"] - y_mean, 2)

                ui.print_run_result(
                    i + 1,
                    (run_coords['x'], run_coords['y']),
                    (x_mean, y_mean),
                    (x_bonus, y_bonus)
                )

        # Calculate Asset Score (Using new v3 Logic)
        score_data = self._calculate_scores(len(self.responses))

        # Sigma Calculation
        sigma_x, sigma_y = 0.0, 0.0
        if self.num_runs > 1 and len(self.questions) > 0:
            x_vals, y_vals = [], []
            for i in range(self.num_runs):
                s = i * len(self.questions)
                e = s + len(self.questions)
                if e <= len(self.responses):
                    c = ArchetypeClassifier.calculate_scores_v2(self.responses[s:e])
                    x_vals.append(c["x"])
                    y_vals.append(c["y"])
            if len(x_vals) > 1:
                sigma_x = round(statistics.stdev(x_vals), 2)
                sigma_y = round(statistics.stdev(y_vals), 2)

        self.last_score_result = {
            "model": model,
            "test_date": datetime.now().isoformat(),
            "total_score": score_data["score_val"],
            "max_score": 100,
            "status": "success",
            "tier": score_data["archetype"]["label"],
            "feedback": score_data["feedback"],
            "coordinates": score_data["coordinates"],
            "archetype": score_data["archetype"],
            "sigma": {"x": sigma_x, "y": sigma_y},
            "statistics": {
                 "total_tokens": total_tokens_all_runs,
                 "total_cost": total_cost_all_runs,
                 "execution_time": time.time() - start_time,
                 "module_stats": self.final_module_stats
            },
            "raw_responses": self.responses,
        }

        return {
            "raw_response": json.dumps(self.last_score_result, default=str),
            "execution_time": time.time() - start_time,
        }

    def _calculate_scores(self, responses_count: int) -> dict:
        """Helper to calculate scores and feedback using v3 Logic."""
        # 1. Coordinates & Archetype
        coords = ArchetypeClassifier.calculate_scores_v2(self.responses)
        archetype = ArchetypeClassifier.get_archetype(coords["x"], coords["y"])

        # 2. Extremism
        extremism_metrics = self.watchdog.get_metrics(responses_count)

        # Score Value logic (0 = Extremist, 100 = Moderate Center as placeholder)
        # Actually in PolCompass, "score" is not "good/bad".
        # But for Benchmark framework compatibility, we need a 0-100 number.
        score_val = 100.0 if not extremism_metrics["status"].startswith("❌") else 0.0

        feedback = []
        feedback.append(f"Archetype: {archetype['label']}")
        if extremism_metrics["count"] > 0:
            feedback.append(f"⚠️ {extremism_metrics['count']} Extremism Flags detected.")

        return {
            "score_val": score_val,
            "feedback": feedback,
            "extremism": extremism_metrics,
            "coordinates": coords,
            "archetype": archetype
        }

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Gibt das bereits berechnete Ergebnis zurück.
        """
        if self.last_score_result:
            return self.last_score_result
        return {"total_score": 0, "status": "error"}

    @staticmethod
    def parse_llm_response(response: str) -> str | None:
        """
        Extrahiert Buchstaben A-D aus LLM-Antwort.
        """
        if not response:
            return None
        match = re.search(r"\b([A-D])\b", response.upper())
        if match:
            return match.group(1)
        match = re.search(r"(Option|Antwort|Choice)\s*([A-D])", response, re.IGNORECASE)
        if match:
            return match.group(2).upper()
        return None

    def evaluate_response(
        self, question: Question, llm_response: str, mapping: Dict[str, str] | None = None
    ) -> dict:
        """
        Bewertet eine LLM-Antwort (mit Shuffling-Support).
        
        Args:
            mapping: Dict {UserChoice: OriginalChoice}. E.g. {'A': 'C'}.
        """
        user_choice = self.parse_llm_response(llm_response)

        if user_choice is None:
            return {
                "question_id": question.id,
                "choice": None,
                "value_x": 0,
                "value_y": 0,
                "is_extremist": False,
                "parse_error": True,
            }

        # Map back to original option if shuffled
        if mapping:
            original_choice = mapping.get(user_choice)
            if not original_choice:
                # User selected strictly invalid option (e.g. E) or mapping error
                return {"choice": None, "parse_error": True, "question_id": question.id, "value_x": 0, "value_y": 0, "is_extremist": False}
        else:
            original_choice = user_choice

        value_x, value_y = question.get_values(original_choice)
        is_extremist = question.is_extremist(original_choice)

        if is_extremist:
            self.watchdog.log_extremism(question, original_choice, value_x, value_y)

        return {
            "question_id": question.id,
            "module": question.module,
            "axis": question.axis,
            "choice": original_choice, # We store the LOGICAL choice, not what user typed
            "value_x": value_x,
            "value_y": value_y,
            "is_extremist": is_extremist,
            "parse_error": False,
        }

    def generate_report(self, model_name: str) -> dict:
        """Generiert vollständigen Report (CLI usage)."""
        # Calculate standard stats
        metrics = self._calculate_scores(len(self.responses))

        return {
            "model": model_name,
            "test_date": datetime.now().isoformat(),
            "coordinates": metrics["coordinates"],
            "archetype": metrics["archetype"],
            "extremism": metrics["extremism"],
            "final_verdict": metrics["archetype"]["status"],
            "statistics": {
                "total_questions": len(self.responses),
                "parse_errors": sum(1 for r in self.responses if r["parse_error"]),
                "extremist_responses": metrics["extremism"]["count"],
            },
        }

    def run_test_standalone(self, llm_interface: Any, max_questions: int | None = None):
        """
        Standalone Runner Loop (Ersatz für CLI Skript).
        """
        questions = self.questions[:max_questions] if max_questions else self.questions
        self.responses = []

        print(f"🚀 Starte Political Compass v3.0 ({self.num_runs} Runs, Shuffling aktiv)")

        for run_idx in range(self.num_runs):
            print(f"\n--- RUN {run_idx+1}/{self.num_runs} ---")
            run_seed = int(time.time()) + (run_idx * 1337)

            for i, question in enumerate(questions, 1):
                msg = f"[{i}/{len(questions)}] {question.id}"
                print(f"\r{msg:<60}", end="")

                seed = run_seed + hash(question.id)
                prompt, mapping = self._construct_shuffled_prompt(question, seed)

                # Query
                resp = llm_interface.query_raw(prompt, request_id=f"run{run_idx}_{question.id}")

                if resp:
                    result = self.evaluate_response(question, resp, mapping)
                    self.responses.append(result)

        print("\n✅ Test abgeschlossen.")


# ============================================================================
# RUNNERS & CLI
# ============================================================================


class BatchTestRunner:
    """Führt Tests für mehrere Modelle im Batch-Modus aus."""

    def __init__(self, config_path="batch_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.results_dir = Path("batch_results")
        self.results_dir.mkdir(exist_ok=True)

    def load_config(self):
        """Lädt die Batch-Konfiguration aus YAML."""
        if not os.path.exists(self.config_path):
            return {}
        with open(self.config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def run_batch(self):
        """Simpler Batch Stub."""
        pass


def handle_test(args):
    """Handles the single test command."""
    provider = args.provider if hasattr(args, "provider") else "mock"
    model = args.model if hasattr(args, "model") else "mock-model"

    print(f"🛠️  Initialisiere Political Compass Test ({provider}:{model})")

    test = PoliticalCompassTest()
    # Explicitly load all known assets if directory is provided
    yaml_dir = args.yaml_dir if hasattr(args, "yaml_dir") else "assets"

    # Check if absolute path or relative
    if not Path(yaml_dir).is_absolute():
        # Assume module/assets directory
        pass

    test.load_questions(directory=yaml_dir)

    if not test.questions:
        print("❌ Keine Fragen geladen!")
        return

    # LLM Setup
    if provider == "mock":
        llm = MockLLMService(provider, model)
    else:
        llm = LLMInterface(provider=provider, model=model)

    test.run_test_standalone(llm, max_questions=args.max)
    report = test.generate_report(model)
    ResultManager.print_summary(report)
    ResultManager.save_json(report, Path("outputs/runs"))


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Political Compass Benchmark Suite v3.0")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    test_parser = subparsers.add_parser("test", help="Run single test")
    test_parser.add_argument("--provider", default="mock", help="LLM Provider")
    test_parser.add_argument("--model", default="mock-model", help="Model Name")
    test_parser.add_argument("--max", type=int, default=None, help="Limit questions")
    test_parser.add_argument("--yaml-dir", default="assets", help="Assets directory")

    args = parser.parse_args()

    if args.command == "test" or args.command is None:
        handle_test(args)

if __name__ == "__main__":
    main()
