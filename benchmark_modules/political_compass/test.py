#!/usr/bin/env python3
"""
Political Compass Test - Core Module v3.0
==========================================

Testet LLMs auf politischen Bias anhand eines Fragekatalogs über 9 Themenmodule.
Integrierte Shuffling-Logik und v3.0 Scoring-Algorithmus.
"""

import json
import re
import os
import time
import statistics
import logging
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from datetime import datetime

import yaml

from utils.benchmark_ui import TerminalUI
from benchmark_modules.base_test import BaseTest
from benchmark_modules.political_compass.core.config import (
    TOPIC_NAMES,
)
from benchmark_modules.political_compass.core.io_manager import CheckpointManager
from benchmark_modules.political_compass.core.models import Question
from benchmark_modules.political_compass.core.evaluators import (
    ArchetypeClassifier,
    ExtremismWatchdog
)
from benchmark_modules.political_compass.core.services import (
    LLMInterface,
    FrameworkAdapter,
    MockLLMService
)
from benchmark_modules.political_compass.core.io_manager import ResultManager
from benchmark_modules.political_compass.core.loader import QuestionLoader
from benchmark_modules.political_compass.core.prompts import PromptBuilder

# Setup basic logging
logging.basicConfig(
    filename="llm_requests.log", level=logging.INFO, format="%(asctime)s - %(message)s"
)


@dataclass
class TestContext:
    """Context object to pass runtime dependencies and state."""
    model: str
    provider: str
    adapter: FrameworkAdapter
    ui: TerminalUI
    total_counters: dict[str, float]


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
        self.responses: list[dict] = []
        self.questions: list[Question] = []
        self.last_score_result: dict[str, Any] = {}
        # Track detailed stats per module across all runs
        self.final_module_stats: dict[str, dict[str, int]] = {}

        # Configuration
        self.num_runs = 3  # Default v3.0 requirement

        # Load config override if available
        try:
            config_path = Path(__file__).parent / "config.yaml"
            if config_path.exists():
                with open(config_path, "r") as f:
                    yaml_content = yaml.safe_load(f)
                    # Check top level or nested config block
                    cfg_block = yaml_content.get("config", {})
                    if "runs" in cfg_block:
                        self.num_runs = int(cfg_block["runs"])
                    elif "runs" in yaml_content: # Fallback legacy
                        self.num_runs = int(yaml_content["runs"])
        except Exception as e:
            logging.warning(f"Could not load political compass config: {e}")

        # Ensure logs directory exists
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        # Setup specific error logger
        self.error_logger = logging.getLogger("political_compass_errors")
        self.error_logger.setLevel(logging.ERROR)
        if not self.error_logger.handlers:
            fh = logging.FileHandler(log_dir / "benchmark_errors.log")
            fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.error_logger.addHandler(fh)



        if asset_path:
            super().__init__(asset_path)
            self.questions = QuestionLoader.load_from_path(asset_path)
        else:
            # Standalone/Batch mode initialization
            self.asset_path = None  # type: ignore
            self.asset = {}

    def load_questions(self, directory: str = "assets") -> int:
        """Lädt alle Fragen aus dem assets-Verzeichnis (für Batch-Modus)."""
        # Pfad-Auflösung: Zuerst relativ zum Modul, Fallback auf direkten Pfad (CWD/Absolut)
        base_path = Path(__file__).parent / directory
        if not base_path.exists():
            direct_path = Path(directory)
            if direct_path.exists():
                base_path = direct_path

        self.questions = QuestionLoader.load_from_directory(base_path)
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

    def _get_block_id(self, question: Question) -> str:
        parts = question.id.split('_')
        code_parts = parts[-1].split('.')
        if len(code_parts) >= 2:
            return f"{code_parts[0]}.{code_parts[1]}"
        return "7.0"

    def _calculate_block_totals(self) -> dict[str, int]:
        block_totals: dict[str, int] = {}
        for q in self.questions:
            block_id = self._get_block_id(q)
            block_totals[block_id] = block_totals.get(block_id, 0) + 1
        return block_totals

    def _finish_block(self, ui: TerminalUI, block_state: dict[str, Any]):
        block_id = block_state["current_id"]
        # Ensure block_id is not None before using it as str
        if block_id is None:
            return

        elapsed = time.time() - block_state["start_time"]
        topic_suffix = TOPIC_NAMES.get(block_id, '').replace(' ', '_').lower()
        full_name = f"{block_id}_{topic_suffix}"

        ui.finish_block(
            full_name,
            elapsed,
            block_state["tokens"],
            block_state["cost"]
        )

        # Aggregate stats
        if block_id not in self.final_module_stats:
            self.final_module_stats[block_id] = {"tokens": 0, "count": 0}
        self.final_module_stats[block_id]["tokens"] += int(block_state["tokens"])
        self.final_module_stats[block_id]["count"] += int(block_state["count"])

    def _process_question_query(
        self,
        question: Question,
        run_seed: int,
        ctx: TestContext,
        block_state: dict[str, Any],
    ):
        # Shuffling Logic per Question
        seed = run_seed + hash(question.id)
        prompt_text, mapping = PromptBuilder.create_shuffled(question, seed)

        # Query Adapter
        raw_resp = None
        try:
            raw_resp = ctx.adapter.client.query(
                model=ctx.model,
                prompt=prompt_text,
                provider=ctx.provider,
                temperature=0.1
            )

            # Track Stats
            cost = getattr(ctx.adapter.client, 'last_request_cost', 0.0) or 0.0
            usage = getattr(ctx.adapter.client, 'last_token_usage', 0) or 0

            block_state["cost"] += cost
            block_state["tokens"] += usage
            ctx.total_counters["cost"] += cost
            ctx.total_counters["tokens"] += usage

        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.error("Error processing question %s: %s", question.id, e)
            print(f"Error processing question {question.id}: {e}")

        block_state["count"] += 1

        if raw_resp:
            # Evaluate with mapping
            result = self.evaluate_response(question, raw_resp, mapping)
            self.responses.append(result)

    def _process_run(
        self,
        run_idx: int,
        ctx: TestContext,
        global_start_offset: int,
    ):
        ctx.ui.start_run(run_idx + 1, self.num_runs, ctx.model, ctx.provider)
        run_seed = int(time.time()) + run_idx

        block_totals = self._calculate_block_totals()

        # State: current_id, count, total, cost, tokens, start_time
        block_state: dict[str, Any] = {
            "current_id": None,
            "count": 0,
            "total": 0,
            "cost": 0.0,
            "tokens": 0,
            "start_time": time.time()
        }

        for q_idx, question in enumerate(self.questions):
        
            # Check Resume Skip
            global_current_idx = global_start_offset + q_idx
            if global_current_idx < len(self.responses):
                continue
                
            block_id = self._get_block_id(question)

            # Check Block Change
            if block_id != block_state["current_id"]:
                # Previous block finished?
                if block_state["current_id"] is not None:
                    self._finish_block(ctx.ui, block_state)

                # Start New Block
                topic_name = TOPIC_NAMES.get(block_id, "Unbekanntes Thema")
                count_in_block = block_totals.get(block_id, 0)
                ctx.ui.start_block(block_id, topic_name, count_in_block)

                block_state["current_id"] = block_id
                block_state["count"] = 0
                block_state["total"] = count_in_block
                block_state["cost"] = 0.0
                block_state["tokens"] = 0
                block_state["start_time"] = time.time()

            self._process_question_query(
                question, run_seed, ctx, block_state
            )

            # Save Checkpoint
            CheckpointManager.save_checkpoint(ctx.model, {
                "responses": self.responses,
                "total_counters": ctx.total_counters,
                "final_module_stats": self.final_module_stats,
                "timestamp": time.time()
            })

            # Progress Line
            ctx.ui.update_progress(
                block_state["count"],
                block_state["total"],
                block_state["tokens"],
                block_state["cost"],
                finished=False
            )

        # End of Run Loop - Close Last Block
        if block_state["current_id"] is not None:
            ctx.ui.update_progress(
                block_state["count"],
                block_state["total"],
                block_state["tokens"],
                block_state["cost"],
                finished=True
            )
            self._finish_block(ctx.ui, block_state)

    def _print_run_summary(self, run_idx: int, run_start_idx: int, ui: TerminalUI):
        """Prints the summary of the current run."""
        run_resps = self.responses[run_start_idx:]
        if run_resps:
            run_coords = ArchetypeClassifier.calculate_scores_v2(run_resps)
            debug_data = run_coords.get("debug", {})
            x_mean = round(debug_data.get("x_mean", 0), 2)
            y_mean = round(debug_data.get("y_mean", 0), 2)
            x_bonus = round(run_coords["x"] - x_mean, 2)
            y_bonus = round(run_coords["y"] - y_mean, 2)

            ui.print_run_result(
                run_idx + 1,
                (run_coords['x'], run_coords['y']),
                (x_mean, y_mean),
                (x_bonus, y_bonus)
            )

    def execute(
        self,
        model: str,
        llm_client: Any,
        provider: str = "ollama",
        **kwargs: Any
    ) -> dict[str, Any]:
        """
        Ausführungsmethode für BenchmarkRunner.
        """
        start_time = time.time()

        # Init specific UI for this module
        ui = TerminalUI()
        
        # Only print intro for the first sub-question of a block to reduce noise
        # Since we don't have global state here easily, we rely on the implementation
        # of TerminalUI or just silence it if it's too frequent.
        # But user reported "re-start" feel. 
        # We will keep it but make it less aggressive or check logging.
        # The user wants "runs: 3". The intro says "Runs: 3".
        
        # To avoid spamming the big header for every single question (since one question = one asset),
        # we check if this looks like the start of a section (e.g. *.001)
        is_start_node = False
        if self.asset and "metadata" in self.asset:
             aid = self.asset["metadata"].get("id", "")
             if aid.endswith(".001"):
                 is_start_node = True
        
        # Always print if no asset (batch mode) or if it is the first question of a section
        if not self.asset or is_start_node:
            intro_info = [
                f"⚠️  WICHTIG: Dieser Benchmark führt {self.num_runs} Runs durch.",
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

        # Track detailed stats per module across all runs
        # Format: "7.1": {"tokens": 0, "count": 0}
        self.final_module_stats = {}

        total_counters: dict[str, float] = {"tokens": 0.0, "cost": 0.0}

        # Check for force_clean via kwargs
        force_clean = kwargs.get("force_new", False) or kwargs.get("force_clean", False)

        # RESUME CHECK
        active_checkpoint = CheckpointManager.load_checkpoint(
            model, 
            force_new=force_clean,
            max_age_hours=48
        )
        if active_checkpoint:
            print(f"🔄 Resuming session for {model}...")
            self.responses = active_checkpoint.get("responses", [])
            saved_counters = active_checkpoint.get("total_counters", {})
            total_counters["tokens"] = saved_counters.get("tokens", 0.0)
            total_counters["cost"] = saved_counters.get("cost", 0.0)
            self.final_module_stats = active_checkpoint.get("final_module_stats", {})
            print(f"   ✓ Loaded {len(self.responses)} previous responses.")
        
        ctx = TestContext(
            model=model,
            provider=provider,
            adapter=adapter,
            ui=ui,
            total_counters=total_counters
        )

        for i in range(self.num_runs):
            run_start_idx = len(self.responses)
            global_start_offset = i * len(self.questions)

            self._process_run(i, ctx, global_start_offset)
            self._print_run_summary(i, run_start_idx, ui)
        
        # Cleanup Checkpoint
        CheckpointManager.clear_checkpoint(model)

        # Calculate Asset Score (Using new v3 Logic)
        score_data = self._calculate_scores(len(self.responses))

        # Sigma Calculation
        sigma_x, sigma_y = 0.0, 0.0
        individual_runs = []
        if self.num_runs > 1 and len(self.questions) > 0:
            x_vals, y_vals = [], []
            for i in range(self.num_runs):
                s = i * len(self.questions)
                e = s + len(self.questions)
                if e <= len(self.responses):
                    c = ArchetypeClassifier.calculate_scores_v2(self.responses[s:e])
                    x_vals.append(c["x"])
                    y_vals.append(c["y"])
                    
                    # Capture Run Data
                    arch = ArchetypeClassifier.get_archetype(c["x"], c["y"])
                    individual_runs.append({
                        "id": i + 1,
                        "x": c["x"],
                        "y": c["y"],
                        "x_label": arch["x_label"],
                        "y_label": arch["y_label"]
                    })
                    
            if len(x_vals) > 1:
                sigma_x = round(statistics.stdev(x_vals), 2)
                sigma_y = round(statistics.stdev(y_vals), 2)

        self.last_score_result = {
            "model": model,
            "test_date": datetime.now().isoformat(),
            "individual_runs": individual_runs,
            "total_score": score_data["score_val"],
            "max_score": 100,
            "status": "success",
            "tier": score_data["archetype"]["label"],
            "feedback": score_data["feedback"],
            "coordinates": score_data["coordinates"],
            "archetype": score_data["archetype"],
            "sigma": {"x": sigma_x, "y": sigma_y},
            "statistics": {
                 "total_tokens": total_counters["tokens"],
                 "total_cost": total_counters["cost"],
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

    def score_response(self, response: str) -> dict[str, Any]:
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
        self,
        question: Question,
        llm_response: str,
        mapping: dict[str, str] | None = None,
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
                return {
                    "choice": None,
                    "parse_error": True,
                    "question_id": question.id,
                    "value_x": 0,
                    "value_y": 0,
                    "is_extremist": False
                }
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
                prompt, mapping = PromptBuilder.create_shuffled(question, seed)

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
