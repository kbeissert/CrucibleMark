#!/usr/bin/env python3
"""Benchmark Runner für kommerzielle API-basierte Modelle."""

import sys
import logging
import json
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Suppress verbose HTTP logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# pylint: disable=wrong-import-position, import-error
from utils.base_runner import BaseBenchmarkRunner
from utils.module_loader import load_test_class
from utils.benchmark_utils import select_from_list, discover_assets, load_asset_yaml
from scripts.run_political_compass_benchmark import run_political_compass_benchmark
# pylint: enable=wrong-import-position, import-error

logger = logging.getLogger(__name__)


class CommercialBenchmarkRunner(BaseBenchmarkRunner):
    """Benchmark Runner für kommerzielle API-basierte Modelle."""

    benchmark_categories: Dict[str, Any] = {}

    def __init__(self, mode: str = 'test', force: bool = False):
        """Initialisiert Runner.

        Args:
            mode: 'golden_standard' oder 'test'
            force: Wenn True, werden existierende Golden Standards überschrieben
        """
        super().__init__()
        self.mode = mode
        self.force = force
        self._load_categories()

    def _load_categories(self):
        """Loads benchmark categories from config."""
        self.benchmark_categories = {}
        if 'modules' in self.validator.config:
            for key, mod in self.validator.config['modules'].items():
                if mod.get('enabled', False):
                    self.benchmark_categories[key] = {
                        'name': mod['name'],
                        'description': mod['description'],
                        'path': f"{mod['path']}/assets",
                        'test_class': mod.get('test_class', 'CodeQualityTest')
                    }

    def get_available_providers(self) -> Dict[str, dict]:
        """Holt aktivierte kommerzielle Provider aus Config."""
        return self.validator.get_enabled_commercial_providers()

    def select_mode(self) -> Optional[str]:
        """Wähle Benchmark-Modus."""
        print(f"\n{'=' * 60}")
        print("🎯 BENCHMARK-MODUS")
        print(f"{'=' * 60}")
        print("  1. Golden Standard generieren (Referenz-Benchmark)")
        print(f"     → Speichert in: {self.validator.get_golden_standard_csv()}")
        print("\n  2. Kommerzielle Modelle testen")
        print("     → Speichert in: commercial_models_benchmark.csv")
        print(f"{'=' * 60}")

        while True:
            try:
                choice = input("\nWähle Modus (1-2): ").strip()
                if choice == '1':
                    print("✓ Golden Standard Mode\n")
                    return 'golden_standard'
                if choice == '2':
                    print("✓ Test Mode\n")
                    return 'test'
                print("❌ Bitte 1 oder 2 eingeben")
            except KeyboardInterrupt:
                print("\n\n❌ Abgebrochen")
                return None

    def select_golden_standard_model(self) -> Optional[Tuple[str, str]]:
        """Holt das Golden Standard Modell aus Config."""
        info = self.validator.get_golden_standard_info()
        if not info:
            print("❌ Kein Golden Standard in Config definiert")
            return None

        provider_key, model_id, provider_config = info
        print(f"\n{'=' * 60}\n🏆 GOLDEN STANDARD MODELL\n{'=' * 60}")
        print(f"Provider: {provider_config.get('name', provider_key)}")
        print(f"Modell:   {model_id}\n{'=' * 60}\n")

        return (provider_key, model_id)

    def select_test_model(self) -> Optional[Tuple[str, str]]:
        """Interaktive Modell-Auswahl für Test Mode."""
        providers = self.get_available_providers()
        model_list = []

        for p_key, p_conf in providers.items():
            p_name = p_conf.get('name', p_key)
            for model in p_conf.get('models', []):
                m_id = model.get('id')
                m_name = model.get('name', m_id)
                desc = model.get('description', '')
                model_list.append((p_key, m_id, p_name, m_name, desc))

        selected = select_from_list(
            model_list,
            lambda item: f"[{item[2]}] {item[3]}" + (f" - {item[4]}" if item[4] else ""),
            prompt="Wähle Modell",
            title="🌐 VERFÜGBARE MODELLE"
        )

        if selected:
            # pylint: disable=unbalanced-tuple-unpacking
            p_key, m_id, p_name, m_name, _ = selected
            print(f"✓ Ausgewählt: {p_name} - {m_name}\n")
            return (p_key, m_id)

        return None

    def select_benchmark(self) -> Optional[Dict[str, Any]]:
        """Interaktive Benchmark-Auswahl."""
        categories = list(self.benchmark_categories.items())
        selected = select_from_list(
            categories,
            lambda item: (item[1]['name'], item[1]['description']),
            prompt="Wähle Benchmark",
            title="📊 VERFÜGBARE BENCHMARKS"
        )
        if selected:
            key, info = selected
            print(f"✓ Ausgewählt: {info['name']}\n")
            return {'key': key, **info}
        return None

    @staticmethod
    def _get_quality_badge(percentage: float) -> str:
        """Deprecated: Use self.get_quality_badge instead."""
        return BaseBenchmarkRunner.get_quality_badge(percentage)

    # pylint: disable=too-many-arguments, too-many-locals, too-many-positional-arguments
    def _recover_from_json(
        self,
        json_path: Path,
        asset_path: Path,
        benchmark_info: Dict[str, Any],
        provider: str,
        model: str
    ) -> Optional[Dict[str, Any]]:
        """Recovers a result from a cached JSON file."""
        try:
            with open(json_path, encoding='utf-8') as f:
                data = json.load(f)

            # Re-calculate score
            module_path = Path(benchmark_info['path']).parent / 'test.py'
            test_cls_name = benchmark_info.get('test_class', 'CodeQualityTest')
            test_cls = load_test_class(module_path, test_cls_name)
            test_inst = test_cls(asset_path)

            score = test_inst.score_response(data.get('response', ''))
            asset_id = data.get('id', asset_path.stem)

            result = {
                'timestamp': data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'status': score.get('status', 'success'),
                'provider': provider,
                'model': model,
                'asset_id': asset_id,
                'asset_name': asset_path.stem,
                'total_score': score['total_score'],
                'max_score': score['max_score'],
                'percentage': round((score['total_score'] / score['max_score'] * 100), 1),
                'execution_time': data.get('execution_time', 0.0),
                'response_length': len(data.get('response', '')),
                'tier': score.get('tier', 'Tier 1')
            }

            for cat, val in score.get('category_scores', {}).items():
                result[cat] = f"{val['achieved']}/{val['max']}"

            return result

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"   ⚠️ Fehler beim Wiederherstellen aus JSON: {e}")
            return None

    # pylint: disable=too-many-arguments, too-many-locals, too-many-positional-arguments
    def _process_single_asset(
        self,
        asset_path: Path,
        provider: str,
        model: str,
        benchmark_info: Dict[str, Any],
        is_golden_model: bool
    ) -> Optional[Dict[str, Any]]:
        """Processes a single asset."""
        asset_data = load_asset_yaml(asset_path)
        if not asset_data:
            print(f"⚠️  Skipping empty asset: {asset_path.name}")
            return None

        asset_id = asset_data.get('metadata', {}).get('id', asset_path.stem)
        asset_name = asset_data.get('metadata', {}).get('name') or \
                     asset_data.get('metadata', {}).get('topic', asset_id)

        json_path = Path(f"golden_standards/{provider}/{asset_id}.json")

        # Check for cached Golden Standard
        if is_golden_model and json_path.exists():
            if self.mode == 'golden_standard' and not self.force:
                print(f"⏭️  Überspringe {asset_name} (Golden Standard existiert)")
                res = self._recover_from_json(
                    json_path, asset_path, benchmark_info, provider, model
                )
                if res:
                    res['asset_name'] = asset_name  # Ensure name is correct
                    print(f"   ✓ Cached: {res['percentage']}%")
                    return res

        print(f"▶️  Teste: {asset_name}...")

        # Execute Test using BaseRunner logic
        try:
            test_inst, exec_result = self.execute_test_module(
                model=model,
                asset_path=asset_path,
                benchmark_info=benchmark_info,
                provider=provider
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"❌ Fehler bei Ausführung: {e}")
            return None

        response = exec_result['raw_response']
        score = test_inst.score_response(response)

        # Build Standardized Result
        result = self.build_base_result(model, asset_data, score, exec_result, provider)

        # Print Output
        badge = self.get_quality_badge(result['percentage'])
        print(f"   Ergebnis: {result['percentage']}% {badge} "
              f"({result['total_score']}/{result['max_score']} Pkt)")

        # Save Golden Standard JSON if needed
        if self.mode == 'golden_standard' or is_golden_model:
            self._save_golden_json(provider, asset_id, response, exec_result['execution_time'])
            if self.mode == 'test' and is_golden_model:
                self._append_to_golden_csv(result)

        return result

    @staticmethod
    def _save_golden_json(
        provider: str, asset_id: str, response: str, execution_time: float
    ):
        """Saves the full response as JSON."""
        output_dir = Path(f"golden_standards/{provider}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{asset_id}.json"

        data = {
            "id": asset_id,
            "provider": provider,
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "response": response
        }
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("   💾 JSON gespeichert.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"   ⚠️  JSON Fehler: {e}")

    def _append_to_golden_csv(self, result: Dict[str, Any]):
        """Appends result to golden CSV."""
        self.result_manager.save_results([result], result_type='golden')
        print("   💾 Auch in Golden Standard CSV gespeichert.")

    def run_benchmark(
        self,
        provider: str,
        model: str,
        benchmark_info: Dict[str, Any],
        num_runs: int = 1
    ) -> List[Dict[str, Any]]:
        """Main benchmark execution loop."""

        # Political Compass Dispatch
        if benchmark_info.get('name') == 'Political Compass':
             # pylint: disable=import-outside-toplevel
            # from scripts.run_political_compass_benchmark import run_political_compass_benchmark
            run_political_compass_benchmark(model, provider, benchmark_info, num_runs=num_runs)
            return []

        # Check Golden Standard Status
        golden_info = self.validator.get_golden_standard_info()
        is_golden_model = False
        if golden_info:
            g_provider, g_model, _ = golden_info
            if provider == g_provider and model == g_model:
                is_golden_model = True

        print(f"\n{'=' * 60}\n📊 STARTE BENCHMARK: {benchmark_info['name']}\n{'=' * 60}")
        print(f"Provider: {provider}\nModell:   {model}\nModus:    {self.mode}")
        if is_golden_model:
            print("ℹ️  Dies ist das Golden Standard Modell.")

        assets = discover_assets(benchmark_info['path'])
        print(f"Tests:    {len(assets)}\n{'=' * 60}\n")

        results = []
        for asset_path in assets:
            res = self._process_single_asset(
                asset_path, provider, model, benchmark_info, is_golden_model
            )
            if res:
                results.append(res)

        return results

    def save_results(self, results: List[Dict[str, Any]]):
        """Saves results to CSV."""
        if not results:
            return

        target = 'commercial'
        if self.mode == 'golden_standard':
            target = 'golden'
            # Also save to commercial for record keeping
            self.result_manager.save_results(results, result_type='commercial')

        path = self.result_manager.save_results(results, result_type=target)
        if path:
            print(f"\n💾 Ergebnisse gespeichert: {path}")

    def print_summary(self, results: List[Dict[str, Any]]):
        """Prints benchmark summary."""
        if not results:
            return

        print(f"\n{'=' * 60}\n📊 ZUSAMMENFASSUNG\n{'=' * 60}")

        total_score = sum(r['total_score'] for r in results)
        max_possible = sum(r['max_score'] for r in results)
        avg_pct = (total_score / max_possible * 100) if max_possible > 0 else 0

        print(f"Gesamt:   {total_score:.1f}/{max_possible} ({avg_pct:.1f}%)")
        print(f"Qualität: {self._get_quality_badge(avg_pct)}\n{'-' * 60}")

        for r in results:
            badge = self._get_quality_badge(r['percentage'])
            print(f"{r['asset_name'][:40]:<40} | {r['percentage']:>5.1f}% | {badge}")
        print(f"{'=' * 60}\n")


def main():
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(description="Commercial Benchmark Runner")
    parser.add_argument('--mode', choices=['golden_standard', 'test'], help="Benchmark mode")
    parser.add_argument('--auto', action='store_true', help="Run automatically without interaction")
    parser.add_argument(
        '--force', action='store_true', help="Force overwrite existing Golden Standards"
    )
    args = parser.parse_args()

    print(f"\n{'=' * 60}\n🚀 KOMMERZIELLE MODELLE BENCHMARK\n{'=' * 60}")

    runner = CommercialBenchmarkRunner()

    # 1. Select Mode
    mode = args.mode or runner.select_mode()
    if not mode:
        return
    runner = CommercialBenchmarkRunner(mode=mode, force=args.force)

    # 2. Select Model
    if mode == 'golden_standard':
        result = runner.select_golden_standard_model()
    else:
        result = runner.select_test_model()

    if not result:
        return

    provider, model_id = result

    # 3. Select Benchmark (or Auto)
    if args.auto:
        print(
            "\n🚀 Starte automatischen Golden Standard Run für alle Module..."
        )
        for _, cat_info in runner.benchmark_categories.items():
            results = runner.run_benchmark(provider, model_id, cat_info)
            runner.save_results(results)
            runner.print_summary(results)
        return

    benchmark_info = runner.select_benchmark()
    if not benchmark_info:
        return

    try:
        results = runner.run_benchmark(provider, model_id, benchmark_info)
        runner.save_results(results)
        runner.print_summary(results)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n❌ Fatal Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
