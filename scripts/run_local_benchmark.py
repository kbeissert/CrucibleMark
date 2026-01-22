#!/usr/bin/env python3
"""Benchmark Runner für lokale Ollama-Modelle."""

import sys
import subprocess
import shutil
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# pylint: disable=wrong-import-position, import-error
from utils.llm_client import LLMClient
from utils.config_validator import ConfigValidator
from utils.result_manager import ResultManager
from utils.benchmark_utils import select_from_list, discover_assets, load_asset_yaml
from utils.module_loader import load_test_class
# pylint: enable=wrong-import-position, import-error

logger = logging.getLogger(__name__)


class LocalBenchmarkRunner:
    """Benchmark Runner für lokale Ollama-Modelle mit Referenz zu kommerziellen Modellen."""

    BENCHMARK_CATEGORIES = {
        'code_quality': {
            'name': 'Code Quality',
            'description': 'WCAG, Security, Performance, API Design, Code Smells',
            'path': 'benchmark_modules/code_quality/assets'
        }
    }

    # Quality thresholds (Adjusted for Hardened Assets v3.0)
    QUALITY_EXCELLENT = 85  # Trophy badge (Weltklasse)
    QUALITY_GOOD = 70       # Star badge (Sehr gut / Brauchbar)
    QUALITY_OK = 55         # Checkmark badge (OK für einfache Tasks)

    def __init__(self):
        """Initialisiert Runner."""
        self.client = LLMClient()
        self.validator = ConfigValidator()
        self.result_manager = ResultManager(self.validator)
        self.commercial_csv = self.validator.get_golden_standard_csv()

    @staticmethod
    def get_ollama_models() -> List[str]:
        """Holt verfügbare Ollama-Modelle."""
        try:
            ollama_path = shutil.which("ollama")
            if not ollama_path:
                print("⚠️  Ollama Executable nicht gefunden.")
                return []

            result = subprocess.run(
                [ollama_path, 'list'],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

            models = []
            for line in result.stdout.strip().split('\n')[1:]:
                if not line.strip():
                    continue
                model_name = line.split()[0]
                name_lower = model_name.lower()
                # Exclude non-generative models
                if not any(x in name_lower for x in ['embed', '-vl', 'vision']):
                    models.append(model_name)

            return sorted(models)

        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"⚠️  Ollama nicht verfügbar: {e}")
            return []

    def load_commercial_references(self) -> Dict[str, Dict[str, Any]]:
        """Lädt kommerzielle Referenzwerte aus CSV."""
        if not self.commercial_csv.exists():
            return {}

        references = {}
        try:
            with open(self.commercial_csv, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    asset_id = row.get('asset_id', '')
                    model = row.get('model', '')
                    if asset_id and model:
                        references[asset_id] = {
                            'model': model,
                            'provider': row.get('provider', ''),
                            'score': float(row.get('total_score', 0)),
                            'percentage': float(row.get('percentage', 0))
                        }
        except (OSError, ValueError) as e:
            logger.warning("Fehler beim Laden der Referenzen: %s", e)

        return references

    def is_reasoning_model(self, model_name: str) -> bool:
        """Prüft auf Reasoning-Modelle (langsam)."""
        triggers = ['deepseek-r1', 'o1', 'reasoning', 'phi4', 'qwq']
        return any(t in model_name.lower() for t in triggers)

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
            title="🤖 Verfügbare lokale Modelle (Ollama)"
        )

        if selected:
            print(f"✓ Ausgewählt: {selected}")
            if self.is_reasoning_model(selected):
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
            lambda item: (item[1]['name'], item[1]['description']),
            prompt="Wähle einen Benchmark",
            title="📊 Verfügbare Benchmarks"
        )
        if selected_item:
            key, info = selected_item
            print(f"✓ Ausgewählt: {info['name']}\n")
            return {'key': key, **info}
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

    def _execute_test(self, model: str, asset_path: Path, benchmark_info: Dict[str, Any]):
        """Executes the test using the dynamically loaded test class."""
        module_path = Path(
            benchmark_info.get('module_path', 'benchmark_modules/code_quality')
        ) / 'test.py'
        test_class_name = benchmark_info.get('test_class', 'CodeQualityTest')

        try:
            test_cls = load_test_class(module_path, test_class_name)
        except (FileNotFoundError, ImportError, AttributeError) as e:
            raise FileNotFoundError(f"Test-Modul fehlerhaft: {module_path} ({e})") from e

        test_instance = test_cls(asset_path)
        return test_instance, test_instance.execute(model, self.client)

    def _create_error_result(self, asset_path: Path, error_message: str) -> Dict[str, Any]:
        """Creates an error result dictionary."""
        return {
            'status': 'error',
            'error_message': error_message,
            'asset_id': asset_path.stem,
            'asset_name': asset_path.stem,
            'percentage': 0,
            'tier': 'Tier 1',
            'execution_time': 0,
            'total_score': 0,
            'max_score': 0
        }

    def _compare_golden(
        self,
        asset_data: Dict[str, Any],
        response: str,
        test_instance: Any
    ) -> Dict[str, Any]:
        """Compares response with golden standard."""
        asset_id = asset_data.get('metadata', {}).get('id', 'unknown')
        golden_config = asset_data.get('golden_standard', {})
        provider = golden_config.get('generate_with', [{}])[0].get('provider', 'mistral')
        golden_path = Path(f'golden_standards/{provider}/{asset_id}.json')
        return test_instance.compare_to_golden_standard(response, golden_path)

    def _process_single_test(
        self,
        model: str,
        asset_path: Path,
        commercial_refs: Dict[str, Dict[str, Any]],
        benchmark_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Führt einzelnen Test aus."""
        asset_data = load_asset_yaml(asset_path)
        if not asset_data:
            return self._create_error_result(asset_path, "Empty/Invalid Asset File")

        try:
            test_instance, exec_result = self._execute_test(model, asset_path, benchmark_info)
        except (FileNotFoundError, ImportError, AttributeError) as e:
            return self._create_error_result(asset_path, str(e))

        response = exec_result['raw_response']
        score = test_instance.score_response(response)

        # Comparisons
        comparison = self._compare_golden(asset_data, response, test_instance)
        asset_id = asset_data.get('metadata', {}).get('id', asset_path.stem)
        ref = commercial_refs.get(asset_id, {})

        # Build Result
        return self._build_result_dict(
            model=model,
            asset_data=asset_data,
            score=score,
            exec_result=exec_result,
            ref=ref,
            comparison=comparison,
            response_preview=response
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
        response_preview: str
    ) -> Dict[str, Any]:
        """Helper to construct the result dictionary."""
        asset_id = asset_data.get('metadata', {}).get('id', 'unknown')
        asset_name = asset_data.get('metadata', {}).get('name') or \
                     asset_data.get('metadata', {}).get('topic', asset_id)

        ref_score = ref.get('score', 0)
        score_diff = score['total_score'] - ref_score if ref_score > 0 else 0

        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': score.get('status', 'success'),
            'model': model,
            'asset_id': asset_id,
            'asset_name': asset_name,
            'total_score': score['total_score'],
            'max_score': score['max_score'],
            'percentage': round((score['total_score'] / score['max_score'] * 100), 1),
            'reference_model': ref.get('model', 'N/A'),
            'reference_score': ref_score,
            'reference_percentage': ref.get('percentage', 0),
            'score_difference': round(score_diff, 1),
            'execution_time': round(exec_result['execution_time'], 1),
            'response_length': len(response_preview),
            'golden_similarity': round(comparison.get('similarity', 0) * 100, 1),
            'tier': score.get('tier', 'Tier 1 (Undefined)'),
            'details': {
                'asset_id': asset_id,
                'tier': score.get('tier', 'Tier 1 (Undefined)')
            }
        }

        if response_preview.startswith("ERROR:"):
            result['error_message'] = response_preview
        elif not response_preview:
            result['error_message'] = "Empty Response"

        # Add category scores
        for cat_name, cat_data in score.get('category_scores', {}).items():
            result[f'{cat_name}'] = f"{cat_data['achieved']}/{cat_data['max']}"

        return result

    def _setup_benchmark_resources(
        self
    ) -> tuple[Dict[str, Dict[str, Any]], bool]:
        """Loads and validates validation/reference resources."""
        is_valid, message = self.validator.validate_golden_standard()
        print(f"\n{'=' * 60}\n🔍 GOLDEN STANDARD VALIDIERUNG\n{'=' * 60}\n{message}\n{'=' * 60}")

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
        self,
        model: str,
        benchmark_info: Dict[str, Any],
        num_runs: int = 1
    ) -> List[Dict[str, Any]]:
        """Führt Benchmark für gewähltes Modell durch."""

        # Dispatch Political Compass
        if benchmark_info.get('name') == 'Political Compass':
            # pylint: disable=import-outside-toplevel, import-error
            from scripts.run_political_compass_benchmark import run_political_compass_benchmark
            run_political_compass_benchmark(model, 'ollama', benchmark_info, num_runs=num_runs)
            return []

        commercial_refs, _ = self._setup_benchmark_resources()

        # Discover
        assets = self.discover_assets(benchmark_info['path'])
        print(f"\n{'=' * 60}\n📊 Starte Benchmark: {benchmark_info['name']}\n{'=' * 60}")
        print(f"Modell: {model}\nTests: {len(assets)}\n{'=' * 60}\n")

        results = []
        print("Fortschritt:")

        for i, asset_path in enumerate(assets, 1):
            asset_name = asset_path.stem.replace('asset_', '').replace('_', ' ').title()
            print(f"   ⏳ [{i}/{len(assets)}] {asset_name}: Test läuft...", end="\r", flush=True)

            try:
                result = self._process_single_test(
                    model, asset_path, commercial_refs, benchmark_info
                )
                results.append(result)
                self._print_result_status(i, len(assets), asset_name, result)
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(" " * 80, end="\r")
                print(f"   ✗ [{i}/{len(assets)}] {asset_name}: Abgebrochen - {str(e)[:50]}")

        return results

    def _print_result_status(self, idx: int, total: int, name: str, result: Dict[str, Any]):
        """Prints the result of a single test line."""
        print(" " * 80, end="\r")

        if result.get('status') == 'error':
            msg = result.get('error_message', 'Error')
            msg_str = f"FAILED ({msg}) | Time: {result['execution_time']}s"
            print(f"   ✗ [{idx}/{total}] {name}: {msg_str}")
            return

        quality = self._get_quality_badge(result['percentage'])
        base_msg = (
            f"   ✓ [{idx}/{total}] {name}: {result['total_score']}/{result['max_score']} "
            f"({result['percentage']}%) {quality}"
        )

        if result.get('reference_score', 0) > 0:
            diff = result['score_difference']
            sym = "+" if diff > 0 else ""
            print(f"{base_msg} | Ref: {result['reference_percentage']}% | Diff: {sym}{diff:.1f}")
        else:
            print(f"{base_msg} | Zeit: {result['execution_time']}s")

    @staticmethod
    def _get_quality_badge(percentage: float) -> str:
        """Gibt Quality-Badge zurück."""
        if percentage >= LocalBenchmarkRunner.QUALITY_EXCELLENT:
            return "🏆"
        if percentage >= LocalBenchmarkRunner.QUALITY_GOOD:
            return "⭐"
        if percentage >= LocalBenchmarkRunner.QUALITY_OK:
            return "✓"
        return "⚠️"

    def save_results(self, results: List[Dict[str, Any]]) -> None:
        """Speichert Ergebnisse in CSV via ResultManager."""
        if not results:
            return
        path = self.result_manager.save_results(results, 'local')
        print(f"\n{'=' * 60}")
        if path:
            print(f"✅ Ergebnisse gespeichert: {path}")
        print(f"{'=' * 60}")

    def print_summary(self, results: List[Dict[str, Any]], model: str) -> None:
        """Druckt Zusammenfassung."""
        if not results:
            return

        successful = [r for r in results if r.get('status') != 'error']
        failed = [r for r in results if r.get('status') == 'error']

        if not successful:
            print(f"\n{'=' * 60}\n📈 BENCHMARK ZUSAMMENFASSUNG\n{'=' * 60}")
            print(f"Modell: {model}\n❌ Alle {len(results)} Tests fehlgeschlagen!")
            return

        # Calculate averages
        avg_score = sum(r['total_score'] for r in successful) / len(successful)
        avg_max = sum(r['max_score'] for r in successful) / len(successful)
        avg_pct = sum(r['percentage'] for r in successful) / len(successful)
        avg_time = sum(r['execution_time'] for r in successful) / len(successful)

        quality = self._get_quality_badge(avg_pct)

        print(f"\n{'=' * 60}\n📈 BENCHMARK ZUSAMMENFASSUNG\n{'=' * 60}")
        print(f"Modell: {model}")
        print(f"Tests: {len(results)} ({len(successful)} ✅, {len(failed)} ❌)")
        print("\n📊 Durchschnitt (erfolgreiche Tests):")
        print(f"   Dein Modell: {avg_score:.1f}/{avg_max:.0f} ({avg_pct:.1f}%) {quality}")
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
        if not results or results[0].get('reference_score', 0) <= 0:
            return

        avg_ref = sum(r.get('reference_score', 0) for r in results) / len(results)
        avg_diff = sum(r.get('score_difference', 0) for r in results) / len(results)

        print(f"   Referenz:    {avg_ref:.1f}/100")
        if avg_diff > 0:
            print(f"   🎯 Differenz: +{avg_diff:.1f} (besser!)")
        elif avg_diff < 0:
            print(f"   📉 Differenz: {avg_diff:.1f} (Gap)")
        else:
            print("   ⚖️  Differenz: ±0")

    def _print_best_worst(self, results: List[Dict[str, Any]]):
        """Prints best and worst performing tests."""
        sorted_res = sorted(results, key=lambda x: x['percentage'], reverse=True)

        print("\n🏆 Beste Tests:")
        for r in sorted_res[:3]:
            q = self._get_quality_badge(r['percentage'])
            d = r.get('score_difference', 0)
            diff_str = f" ({d:+.1f})" if d != 0 else ""
            print(f"   {r['asset_name'][:35]:<35}: {r['percentage']}% {q}{diff_str}")

        print("\n⚠️  Schwächste Tests:")
        for r in sorted_res[-3:]:
            q = self._get_quality_badge(r['percentage'])
            d = r.get('score_difference', 0)
            diff_str = f" ({d:+.1f})" if d != 0 else ""
            print(f"   {r['asset_name'][:35]:<35}: {r['percentage']}% {q}{diff_str}")

    def _print_tiered_analysis(self, results: List[Dict[str, Any]]):
        """Prints Tiered Reasoning Analysis if applicable."""
        reasoning_res = [
            r for r in results
            if r.get('details', {}).get('asset_id', '').startswith('reasoning_')
        ]
        if not reasoning_res:
            return

        print(f"\n🧠 REASONING ANALYSIS (Tiered)\n{'-' * 60}")
        t1_scores = [
            r['total_score'] for r in reasoning_res
            if 'Tier 1' in r.get('details', {}).get('tier', 'Tier 1')
        ]
        t2_scores = [
            r['total_score'] for r in reasoning_res
            if 'Tier 2' in r.get('details', {}).get('tier', '')
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


if __name__ == '__main__':
    main()
