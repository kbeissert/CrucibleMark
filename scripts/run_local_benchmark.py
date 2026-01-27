#!/usr/bin/env python3
"""Benchmark Runner für lokale Ollama-Modelle."""

import sys
import subprocess
import shutil
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# pylint: disable=wrong-import-position, import-error
from utils.base_runner import BaseBenchmarkRunner
from utils.benchmark_utils import select_from_list, discover_assets, load_asset_yaml
from utils.module_loader import load_test_class
from utils.model_utils import is_reasoning_model
# pylint: enable=wrong-import-position, import-error

logger = logging.getLogger(__name__)


class LocalBenchmarkRunner(BaseBenchmarkRunner):
    """Benchmark Runner für lokale Ollama-Modelle."""

    def __init__(self):
        """Initialisiert Runner."""
        super().__init__()
        self.commercial_csv = self.validator.get_golden_standard_csv()
        
        # Load modules from config
        self.BENCHMARK_CATEGORIES = {}
        modules_config = self.validator.config.get("modules", {})
        
        for key, mod in modules_config.items():
            if mod.get("enabled", False):
                self.BENCHMARK_CATEGORIES[key] = {
                    "name": mod["name"],
                    "description": mod["description"],
                    "path": f"{mod['path']}/assets",
                    "module_path": mod["path"],
                    "test_class": mod.get("test_class", "CodeQualityTest"),
                    "execution_mode": mod.get("execution_mode", "standard"),
                    "min_runs": mod.get("min_runs", 1),
                }


    @staticmethod
    def get_ollama_models() -> List[str]:
        """Holt verfügbare Ollama-Modelle."""
        try:
            ollama_path = shutil.which("ollama")
            if not ollama_path:
                print("⚠️  Ollama Executable nicht gefunden.")
                return []

            result = subprocess.run(
                [ollama_path, "list"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            models = []
            for line in result.stdout.strip().split("\n")[1:]:
                if not line.strip():
                    continue
                model_name = line.split()[0]
                name_lower = model_name.lower()
                # Exclude non-generative models
                if not any(x in name_lower for x in ["embed", "-vl", "vision"]):
                    models.append(model_name)

            return sorted(models)

        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ) as e:
            print(f"⚠️  Ollama nicht verfügbar: {e}")
            return []

    def load_commercial_references(self) -> Dict[str, Dict[str, Any]]:
        """Lädt kommerzielle Referenzwerte aus CSV."""
        if not self.commercial_csv.exists():
            return {}

        references = {}
        try:
            with open(self.commercial_csv, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    asset_id = row.get("asset_id", "")
                    model = row.get("model", "")
                    if asset_id and model:
                        references[asset_id] = {
                            "model": model,
                            "provider": row.get("provider", ""),
                            "score": float(row.get("total_score", 0)),
                            "percentage": float(row.get("percentage", 0)),
                        }
        except (OSError, ValueError) as e:
            logger.warning("Fehler beim Laden der Referenzen: %s", e)

        return references

    def select_model(self) -> Optional[str]:
        """Interaktive Modell-Auswahl."""
        models = self.get_ollama_models()
        if not models:
            print("\n❌ Keine Ollama-Modelle gefunden!")
            print("Installiere Modelle mit: ollama pull qwen2.5-coder:7b-instruct")
            return None

        selected = select_from_list(
            models,
            lambda m: m,
            prompt="Wähle ein Modell",
            title="🤖 Verfügbare lokale Modelle (Ollama)",
        )

        if selected:
            print(f"✓ Ausgewählt: {selected}")
            if is_reasoning_model(selected):
                print("\n⚠️  ACHTUNG: Reasoning-Modell erkannt!")
                print("   Diese Modelle nutzen Chain-of-Thought (Denkprozess).")
                print("   Die Ausführung wird signifikant länger dauern!")
            print("")
        return selected

    def select_benchmark(self) -> Optional[Dict[str, Any]]:
        """Interaktive Benchmark-Auswahl."""
        categories = list(self.BENCHMARK_CATEGORIES.items())
        selected_item = select_from_list(
            categories,
            lambda item: (item[1]["name"], item[1]["description"]),
            prompt="Wähle einen Benchmark",
            title="📊 Verfügbare Benchmarks",
        )
        if selected_item:
            key, info = selected_item
            print(f"✓ Ausgewählt: {info['name']}\n")
            return {"key": key, **info}
        return None

    def discover_assets(self, category_path: str) -> List[Path]:
        """Findet alle Assets in einer Kategorie."""
        assets = discover_assets(category_path)
        if not assets:
            path_obj = Path(category_path)
            if not path_obj.exists():
                raise ValueError(f"Kategorie-Pfad nicht gefunden: {category_path}")
            raise ValueError(f"Keine Assets gefunden in: {category_path}")
        return assets

    def _execute_test(
        self, model: str, asset_path: Path, benchmark_info: Dict[str, Any]
    ):
        """Executes the test using the dynamically loaded test class."""
        return self.execute_test_module(
            model, asset_path, benchmark_info, provider="ollama"
        )

    def _create_error_result(
        self, asset_path: Path, error_message: str
    ) -> Dict[str, Any]:
        """Creates an error result dictionary."""
        return {
            "status": "error",
            "error_message": error_message,
            "asset_id": asset_path.stem,
            "asset_name": asset_path.stem,
            "percentage": 0,
            "tier": "Tier 1",
            "execution_time": 0,
            "total_score": 0,
            "max_score": 0,
        }

    def _compare_golden(
        self, asset_data: Dict[str, Any], response: str, test_instance: Any
    ) -> Dict[str, Any]:
        """Compares response with golden standard."""
        asset_id = asset_data.get("metadata", {}).get("id", "unknown")
        golden_config = asset_data.get("golden_standard", {})
        provider = golden_config.get("generate_with", [{}])[0].get(
            "provider", "mistral"
        )
        golden_path = Path(f"golden_standards/{provider}/{asset_id}.json")
        return test_instance.compare_to_golden_standard(response, golden_path)

    def _process_single_test(
        self,
        model: str,
        asset_path: Path,
        commercial_refs: Dict[str, Dict[str, Any]],
        benchmark_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Führt einzelnen Test aus."""
        asset_data = load_asset_yaml(asset_path)
        if not asset_data:
            return self._create_error_result(asset_path, "Empty/Invalid Asset File")

        try:
            test_instance, exec_result = self._execute_test(
                model, asset_path, benchmark_info
            )
        except (FileNotFoundError, ImportError, AttributeError) as e:
            return self._create_error_result(asset_path, str(e))

        response = exec_result["raw_response"]
        score = test_instance.score_response(response)

        # Comparisons
        comparison = self._compare_golden(asset_data, response, test_instance)
        asset_id = asset_data.get("metadata", {}).get("id", asset_path.stem)
        ref = commercial_refs.get(asset_id, {})

        # Build Result
        return self._build_result_dict(
            model=model,
            asset_data=asset_data,
            score=score,
            exec_result=exec_result,
            ref=ref,
            comparison=comparison,
            response_preview=response,
        )

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def _build_result_dict(
        self,
        model: str,
        asset_data: Dict[str, Any],
        score: Dict[str, Any],
        exec_result: Dict[str, Any],
        ref: Dict[str, Any],
        comparison: Dict[str, Any],
        response_preview: str,
    ) -> Dict[str, Any]:
        """Helper to construct the result dictionary."""
        # Use base runner implementation
        result = self.build_base_result(model, asset_data, score, exec_result, "ollama")

        # Add Token Usage (Prefer centralized tracking from client)
        if hasattr(self.client, "last_token_usage"):
            result["tokens_used"] = self.client.last_token_usage
        else:
            result["tokens_used"] = exec_result.get("tokens_used", 0)

        # Add local benchmark specifics
        # FIX: Use percentage for Gap calculation to ensure consistency (0-100 scale)
        # Old: ref_score = ref.get("score", 0) -> used total points which varied
        ref_score = ref.get("percentage", 0)
        score_diff = result["percentage"] - ref_score if ref_score > 0 else 0

        result.update(
            {
                "reference_model": ref.get("model", "N/A"),
                "reference_score": ref_score,
                "reference_percentage": ref.get("percentage", 0),
                "score_difference": round(score_diff, 1),
                "golden_similarity": round(comparison.get("similarity", 0) * 100, 1),
                "details": {"asset_id": result["asset_id"], "tier": result["tier"]},
            }
        )

        if response_preview.startswith("ERROR:"):
            result["error_message"] = response_preview
        elif not response_preview:
            result["error_message"] = "Empty Response"

        # Ensure tier is set if missing (legacy field support)
        if "tier" not in result:
            result["tier"] = "Tier 1 (Undefined)"

        return result

    def _setup_benchmark_resources(self) -> tuple[Dict[str, Dict[str, Any]], bool]:
        """Loads and validates validation/reference resources."""
        is_valid, message = self.validator.validate_golden_standard()
        print(
            f"\n{'=' * 60}\n🔍 GOLDEN STANDARD VALIDIERUNG\n{'=' * 60}\n{message}\n{'=' * 60}"
        )

        commercial_refs = self.load_commercial_references()
        if commercial_refs:
            print(f"\n📌 Golden Standard Scores geladen: {len(commercial_refs)} Assets")
            first_asset = list(commercial_refs.values())[0]
            print(f"   Referenz: {first_asset['model']} ({first_asset['provider']})")
        elif is_valid:
            print("\n⚠️  Golden Standard CSV noch nicht vorhanden.")
        else:
            print("\n⚠️  Golden Standard nicht verfügbar.")

        return commercial_refs, is_valid

    def run_benchmark(
        self, model: str, benchmark_info: Dict[str, Any], num_runs: int = 1
    ) -> List[Dict[str, Any]]:
        """Führt Benchmark für gewähltes Modell durch."""

        # Dispatch Batch Mode (e.g. Political Compass) via Config
        if benchmark_info.get("execution_mode") == "batch":
            # Dynamic Loading
            module_path = Path(benchmark_info.get("module_path", ""))
            test_file = module_path / "test.py"
            test_class_name = benchmark_info.get("test_class")
            
            try:
                TestClass = load_test_class(test_file, test_class_name)
            except Exception as e:
                logger.error("Failed to load batch module %s: %s", benchmark_info['name'], e)
                return []

            # TODO: Generic ResultManager for batch modules
            # For now, we assume Political Compass structure for batch mode
            # Ideally, the TestClass should handle IO or return a standard object
            from benchmark_modules.political_compass.core.io_manager import ResultManager
            from utils.llm_client import LLMClient
            import json

            print(f"🛠️  Initialisiere Batch-Test: {benchmark_info['name']} ({model})")
            test = TestClass()
            
            # Load assets dynamically from module path
            assets_dir = module_path / "assets"
            if not assets_dir.exists():
                print(f"❌ Assets directory not found: {assets_dir}")
                return []
                
            if hasattr(test, "load_questions"):
                test.load_questions(str(assets_dir))
            
            if hasattr(test, "questions") and not test.questions:
                print("❌ Keine Fragen geladen!")
                return []
                
            # Apply runs config
            min_runs = benchmark_info.get("min_runs", 1)
            test.num_runs = max(num_runs, min_runs)
            
            # Use LLMClient from utils
            client = LLMClient(config=self.validator.config)

            # Execution
            result_wrapper = test.execute(model=model, llm_client=client, provider="ollama")
            
            # Reporting
            report = json.loads(result_wrapper["raw_response"])
            ResultManager.print_summary(report)
            
            # Save results to outputs/runs/
            output_dir = Path("outputs/runs")
            ResultManager.save_json(report, output_dir)

            # Save to shared CSV for Leaderboard
            pc_csv = Path("benchmark_scores/political_compass_results.csv")
            pc_csv.parent.mkdir(exist_ok=True, parents=True)
            
            # Read logic for existing file to append/update
            pc_rows = []
            if pc_csv.exists():
                with open(pc_csv, "r", encoding="utf-8") as f:
                    pc_rows = list(csv.DictReader(f))
            
            # Remove old entry for this model if exists
            pc_rows = [r for r in pc_rows if r.get("model") != model]
            
            new_row = {
                "model": model,
                "run_id": "AVG",
                "x_coordinate": report["coordinates"]["x"],
                "y_coordinate": report["coordinates"]["y"],
                "x_label": report["archetype"]["x_label"],
                "y_label": report["archetype"]["y_label"],
                "timestamp": datetime.now().isoformat()
            }
            pc_rows.append(new_row)
            
            with open(pc_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=new_row.keys())
                writer.writeheader()
                writer.writerows(pc_rows)
            
            # Create Standard Result for CSV
            std_result = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": report.get("status", "success"),
                "provider": "ollama",
                "model": model,
                "asset_id": "political_compass_v3",
                "asset_name": "Political Compass",
                "total_score": report["total_score"],
                "max_score": 100,
                "percentage": report["total_score"],
                "execution_time": round(result_wrapper.get("execution_time", 0), 1),
                "response_length": 0,
                "tier": report.get("tier", "N/A"),
                "cost_usd": report.get("statistics", {}).get("total_cost", 0.0),
                "tokens": report.get("statistics", {}).get("total_tokens", 0)
            }
            return [std_result]

        commercial_refs, _ = self._setup_benchmark_resources()

        # Discover
        assets = self.discover_assets(benchmark_info["path"])
        print(
            f"\n{'=' * 60}\n📊 Starte Benchmark: {benchmark_info['name']}\n{'=' * 60}"
        )
        print(f"Modell: {model}\nTests: {len(assets)}\n{'=' * 60}\n")

        results = []
        print("Fortschritt:")

        for i, asset_path in enumerate(assets, 1):
            asset_name = asset_path.stem.replace("asset_", "").replace("_", " ").title()
            print(
                f"   ⏳ [{i}/{len(assets)}] {asset_name}: Test läuft...",
                end="\r",
                flush=True,
            )

            try:
                result = self._process_single_test(
                    model, asset_path, commercial_refs, benchmark_info
                )
                results.append(result)
                self._print_result_status(i, len(assets), asset_name, result)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(" " * 80, end="\r")
                print(
                    f"   ✗ [{i}/{len(assets)}] {asset_name}: Abgebrochen - {str(e)[:50]}"
                )

        return results

    def _print_result_status(
        self, idx: int, total: int, name: str, result: Dict[str, Any]
    ):
        """Prints the result of a single test line."""
        print(" " * 80, end="\r")

        if result.get("status") == "error":
            msg = result.get("error_message", "Error")
            msg_str = f"FAILED ({msg}) | Time: {result['execution_time']}s"
            print(f"   ✗ [{idx}/{total}] {name}: {msg_str}")
            return

        quality = self.get_quality_badge(result["percentage"])

        # Format tokens
        t_count = result.get("tokens_used", 0)
        token_str = f"{t_count / 1000:.1f}k T" if t_count > 1000 else f"{t_count} T"

        base_msg = (
            f"   ✓ [{idx}/{total}] {name:<25}: {result['percentage']:>5.1f}% {quality} "
        )

        if result.get("reference_score", 0) > 0:
            diff = result["score_difference"]
            sym = "+" if diff > 0 else ""
            # e.g. | vs Ref: +2.0 🟢 | 1.2k T | 12.3s
            icon = "🟢" if diff >= 0 else "🔴"
            print(
                f"{base_msg}| vs Ref: {sym}{diff:.1f} {icon} | {token_str:>7} | {result['execution_time']:>5.1f}s"
            )
        else:
            print(f"{base_msg}| {token_str:>7} | {result['execution_time']:>5.1f}s")

    def save_results(self, results: List[Dict[str, Any]]) -> None:
        """Speichert Ergebnisse in CSV via ResultManager."""
        self.result_manager.save_results(results, result_type="local")

    def print_summary(self, results: List[Dict[str, Any]], model: str) -> None:
        """Druckt Zusammenfassung."""
        if not results:
            return

        successful = [r for r in results if r.get("status") != "error"]
        failed = [r for r in results if r.get("status") == "error"]

        if not successful:
            print(f"\n{'=' * 60}\n📈 BENCHMARK ZUSAMMENFASSUNG\n{'=' * 60}")
            print(f"Modell: {model}\n❌ Alle {len(results)} Tests fehlgeschlagen!")
            return

        # Calculate averages (excluding Political Compass if it's the only test)
        # Filter out political compass for average score calculation because it's qualitative
        scored_results = [
            r for r in successful 
            if not str(r.get("asset_id", "")).startswith("political_compass")
        ]
        
        if not scored_results:
             # If only Political Compass ran
             avg_time = sum(r["execution_time"] for r in successful) / len(successful)
             print(f"\n✅ Benchmark abgeschlossen für Modul: Political Compass")
             print(f"   Modell: {model}")
             print(f"   Dauer:  {avg_time:.1f}s")
             
             # Print specific PC info instead of score
             for r in successful:
                  if "tier" in r:
                       print(f"   Resultat: {r['tier']}")
             
             return

        avg_score = sum(r["total_score"] for r in scored_results) / len(scored_results)
        avg_max = sum(r["max_score"] for r in scored_results) / len(scored_results)
        avg_pct = sum(r["percentage"] for r in scored_results) / len(scored_results)
        avg_time = sum(r["execution_time"] for r in successful) / len(successful)


        quality = self.get_quality_badge(avg_pct)

        print(f"\n✅ Modul abgeschlossen: {model}")
        print(f"Tests: {len(results)} ({len(successful)} ✅, {len(failed)} ❌)")
        print("\n📊 Durchschnitt (erfolgreiche Tests des Moduls):")
        print(
            f"   Dein Modell: {avg_score:.1f}/{avg_max:.0f} ({avg_pct:.1f}%) {quality}"
        )
        print(f"   Zeit: {avg_time:.1f}s")

        self._print_reference_comparison(successful)
        self._print_best_worst(successful)
        self._print_tiered_analysis(successful)

        if failed:
            print("\n❌ Fehlgeschlagen:")
            for r in failed:
                print(f"   {r['asset_name'][:40]}: {r.get('error_message')}")
        print(f"{'=' * 60}")

    def _print_reference_comparison(self, results: List[Dict[str, Any]]):
        """Prints comparison to commercial reference."""
        if not results or results[0].get("reference_score", 0) <= 0:
            return

        avg_ref = sum(r.get("reference_score", 0) for r in results) / len(results)
        avg_diff = sum(r.get("score_difference", 0) for r in results) / len(results)

        print(f"   Referenz:    {avg_ref:.1f}/100")
        if avg_diff > 0:
            print(f"   🎯 Differenz: +{avg_diff:.1f} (besser!)")
        elif avg_diff < 0:
            print(f"   📉 Differenz: {avg_diff:.1f} (Gap)")
        else:
            print("   ⚖️  Differenz: ±0")

    def _print_best_worst(self, results: List[Dict[str, Any]]):
        """Prints best and worst performing tests."""
        if not results:
            return

        sorted_res = sorted(results, key=lambda x: x["percentage"], reverse=True)

        print("\n🏆 Beste Tests:")
        for r in sorted_res[:3]:
            q = self.get_quality_badge(r["percentage"])
            d = r.get("score_difference", 0)
            diff_str = f" ({d:+.1f})" if d != 0 else ""
            print(f"   {r['asset_name'][:35]:<35}: {r['percentage']}% {q}{diff_str}")

        print("\n⚠️  Schwächste Tests:")
        for r in sorted_res[-3:]:
            q = self.get_quality_badge(r["percentage"])
            d = r.get("score_difference", 0)
            diff_str = f" ({d:+.1f})" if d != 0 else ""
            print(f"   {r['asset_name'][:35]:<35}: {r['percentage']}% {q}{diff_str}")

    def _print_tiered_analysis(self, results: List[Dict[str, Any]]):
        """Prints Tiered Reasoning Analysis if applicable."""
        reasoning_res = [
            r
            for r in results
            if r.get("details", {}).get("asset_id", "").startswith("reasoning_")
        ]
        if not reasoning_res:
            return

        print(f"\n🧠 REASONING ANALYSIS (Tiered)\n{'-' * 60}")
        t1_scores = [
            r["total_score"]
            for r in reasoning_res
            if "Tier 1" in r.get("details", {}).get("tier", "Tier 1")
        ]
        t2_scores = [
            r["total_score"]
            for r in reasoning_res
            if "Tier 2" in r.get("details", {}).get("tier", "")
        ]

        t1_avg = sum(t1_scores) / len(t1_scores) if t1_scores else 0
        t2_avg = sum(t2_scores) / len(t2_scores) if t2_scores else 0

        profile = "⚖️  Balanced / Standard"
        if t2_avg >= 80:
            profile = "🧠  Deep Thinker (Complex Logic Expert)"
        elif t1_avg >= 80:
            profile = "🏎️  Daily Driver (Fast & Reliable)"
        elif t1_avg < 50:
            profile = "⚠️  Needs Improvement"

        print(f"   Tier 1 (Operational): {t1_avg:.1f}%")
        print(f"   Tier 2 (Deep Logic):  {t2_avg:.1f}%")
        print(f"   Profile: {profile}\n{'-' * 60}")


def main():
    """CLI Entry Point."""
    runner = LocalBenchmarkRunner()
    print(f"\n{'=' * 60}\n🚀 LOKALE MODELLE BENCHMARK\n{'=' * 60}")

    model = runner.select_model()
    if not model:
        sys.exit(1)

    benchmark = runner.select_benchmark()
    if not benchmark:
        sys.exit(1)

    try:
        results = runner.run_benchmark(model, benchmark)
        runner.save_results(results)
        runner.print_summary(results, model)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n❌ Fehler beim Benchmark: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
    print(f"\n{'=' * 60}")
    print("🏁 BENCHMARK ABGESCHLOSSEN")
    print("Alle Ergebnisse wurden in den Benchmark Scores erfasst.")
    print(f"{'=' * 60}\n")

