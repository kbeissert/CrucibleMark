#!/usr/bin/env python3
"""Benchmark Runner für lokale Ollama-Modelle."""

import sys
import subprocess
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import yaml
# tqdm removed as we use custom printing now

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.llm_client import LLMClient
from utils.config_validator import ConfigValidator
from utils.result_manager import ResultManager


class LocalBenchmarkRunner:
    """Benchmark Runner für lokale Ollama-Modelle mit Referenz zu kommerziellen Modellen."""
    
    BENCHMARK_CATEGORIES = {
        'code_quality': {
            'name': 'Code Quality',
            'description': 'WCAG, Security, Performance, API Design, Code Smells',
            'path': 'benchmark_modules/code_quality/assets'
        }
    }
    
    def __init__(self):
        """Initialisiert Runner."""
        self.client = LLMClient()
        self.validator = ConfigValidator()
        self.result_manager = ResultManager(self.validator)
        
        # Golden Standard CSV aus Config holen
        self.commercial_csv = self.validator.get_golden_standard_csv()
    
    @staticmethod
    def get_ollama_models() -> List[str]:
        """Holt verfügbare Ollama-Modelle."""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            models = []
            for line in result.stdout.strip().split('\n')[1:]:
                if line.strip():
                    model_name = line.split()[0]
                    # Filtere Embedding- und Vision-Modelle aus
                    name_lower = model_name.lower()
                    if 'embed' not in name_lower and '-vl' not in name_lower and 'vision' not in name_lower:
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
        
        with open(self.commercial_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                asset_id = row.get('asset_id', '')
                model = row.get('model', '')
                
                if asset_id and model:
                    # Speichere besten Score pro Asset (z.B. letzter Eintrag = neuester)
                    references[asset_id] = {
                        'model': model,
                        'provider': row.get('provider', ''),
                        'score': float(row.get('total_score', 0)),
                        'percentage': float(row.get('percentage', 0))
                    }
        
        return references
    
    def select_model(self) -> Optional[str]:
        """Interaktive Modell-Auswahl."""
        models = self.get_ollama_models()
        
        if not models:
            print("\n❌ Keine Ollama-Modelle gefunden!")
            print("Installiere Modelle mit: ollama pull qwen2.5-coder:7b-instruct")
            return None
        
        print(f"\n{'='*60}")
        print("🤖 Verfügbare lokale Modelle (Ollama)")
        print(f"{'='*60}")
        
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model}")
        
        print(f"{'='*60}")
        
        while True:
            try:
                choice = input(f"\nWähle ein Modell (1-{len(models)}): ").strip()
                
                if not choice:
                    print("❌ Keine Eingabe - Abbruch")
                    return None
                
                idx = int(choice) - 1
                
                if 0 <= idx < len(models):
                    selected = models[idx]
                    print(f"✓ Ausgewählt: {selected}\n")
                    return selected
                else:
                    print(f"❌ Bitte Zahl zwischen 1 und {len(models)} eingeben")
            
            except ValueError:
                print("❌ Ungültige Eingabe - bitte Zahl eingeben")
            except KeyboardInterrupt:
                print("\n\n❌ Abgebrochen")
                return None
    
    def select_benchmark(self) -> Optional[Dict[str, Any]]:
        """Interaktive Benchmark-Auswahl."""
        print(f"\n{'='*60}")
        print("📊 Verfügbare Benchmarks")
        print(f"{'='*60}")
        
        categories = list(self.BENCHMARK_CATEGORIES.items())
        
        for i, (key, info) in enumerate(categories, 1):
            print(f"  {i}. {info['name']}")
            print(f"     {info['description']}")
            print()
        
        print(f"{'='*60}")
        
        while True:
            try:
                choice = input(f"Wähle einen Benchmark (1-{len(categories)}): ").strip()
                
                if not choice:
                    print("❌ Keine Eingabe - Abbruch")
                    return None
                
                idx = int(choice) - 1
                
                if 0 <= idx < len(categories):
                    key, info = categories[idx]
                    print(f"✓ Ausgewählt: {info['name']}\n")
                    return {'key': key, **info}
                else:
                    print(f"❌ Bitte Zahl zwischen 1 und {len(categories)} eingeben")
            
            except ValueError:
                print("❌ Ungültige Eingabe - bitte Zahl eingeben")
            except KeyboardInterrupt:
                print("\n\n❌ Abgebrochen")
                return None
    
    def discover_assets(self, category_path: str) -> List[Path]:
        """Findet alle Assets in einer Kategorie."""
        category_dir = Path(category_path)
        
        if not category_dir.exists():
            raise ValueError(f"Kategorie-Pfad nicht gefunden: {category_dir}")
        
        assets = sorted(category_dir.glob('*.yaml'))
        
        if not assets:
            raise ValueError(f"Keine Assets gefunden in: {category_dir}")
        
        return assets
    
    def _process_single_test(
        self,
        model: str,
        asset_path: Path,
        commercial_refs: Dict[str, Dict[str, Any]],
        benchmark_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Führt einzelnen Test aus."""
        with open(asset_path, 'r', encoding='utf-8') as f:
            asset_data = yaml.safe_load(f)
        
        # Dynamisches Laden der Test-Klasse
        module_path = Path(benchmark_info.get('module_path', 'benchmark_modules/code_quality')) / 'test.py'
        test_class_name = benchmark_info.get('test_class', 'CodeQualityTest')
        
        from utils.module_loader import load_test_class
        try:
            TestClass = load_test_class(module_path, test_class_name)
        except (FileNotFoundError, ImportError, AttributeError) as e:
             raise FileNotFoundError(f"Test-Modul nicht gefunden oder fehlerhaft: {module_path} ({e})")
        
        test = TestClass(asset_path)
        
        # Execute
        exec_result = test.execute(model, self.client)
        response = exec_result['raw_response']
        execution_time = exec_result['execution_time']
        
        # Score
        score = test.score_response(response)
        
        # Golden standard comparison (für Similarity)
        asset_id = asset_data['metadata']['id']
        golden_config = asset_data.get('golden_standard', {})
        provider = golden_config.get('generate_with', [{}])[0].get('provider', 'mistral')
        golden_path = Path(f'golden_standards/{provider}/{asset_id}.json')
        
        comparison = test.compare_to_golden_standard(response, golden_path)
        
        # Commercial reference
        ref = commercial_refs.get(asset_id, {})
        ref_model = ref.get('model', 'N/A')
        ref_score = ref.get('score', 0)
        ref_percentage = ref.get('percentage', 0)
        
        # Calculate difference
        score_diff = score['total_score'] - ref_score if ref_score > 0 else 0
        
        # Return result
        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': score.get('status', 'success'),
            'model': model,
            'asset_id': asset_id,
            'asset_name': asset_data['metadata']['name'],
            'total_score': score['total_score'],
            'max_score': score['max_score'],
            'percentage': round((score['total_score'] / score['max_score'] * 100), 1),
            'reference_model': ref_model,
            'reference_score': ref_score,
            'reference_percentage': ref_percentage,
            'score_difference': round(score_diff, 1),
            'execution_time': round(execution_time, 1),
            'response_length': len(response),
            'golden_similarity': round(comparison.get('similarity', 0) * 100, 1)
        }
        
        if response.startswith("ERROR:"):
            result['error_message'] = response
        elif not response:
            result['error_message'] = "Empty Response"
        
        # Add category scores
        for cat_name, cat_data in score['category_scores'].items():
            result[f'{cat_name}'] = f"{cat_data['achieved']}/{cat_data['max']}"
        
        return result
    
    def run_benchmark(
        self,
        model: str,
        benchmark_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Führt Benchmark für gewähltes Modell durch."""
        # Validiere Golden Standard Konfiguration
        is_valid, message = self.validator.validate_golden_standard()
        print(f"\n{'='*60}")
        print("🔍 GOLDEN STANDARD VALIDIERUNG")
        print(f"{'='*60}")
        print(message)
        print(f"{'='*60}")
        
        # Load commercial references
        commercial_refs = self.load_commercial_references()
        
        if commercial_refs:
            print(f"\n📌 Golden Standard Scores geladen: {len(commercial_refs)} Assets")
            # Zeige Beispiel-Scores
            first_asset = list(commercial_refs.values())[0]
            print(f"   Referenz-Modell: {first_asset['model']} ({first_asset['provider']})")
            print("   Beispiel-Scores: ", end="")
            scores_preview = [str(int(v['score'])) for v in list(commercial_refs.values())[:3]]
            print(", ".join(scores_preview) + " Punkte...")
        elif is_valid:
            print(f"\n⚠️  Golden Standard CSV noch nicht vorhanden: {self.commercial_csv}")
            print("   Generiere mit: python scripts/run_commercial_benchmark.py")
        else:
            print("\n⚠️  Golden Standard nicht verfügbar (siehe Validierung oben)")
        
        # Discover assets
        assets = self.discover_assets(benchmark_info['path'])
        
        print(f"\n{'='*60}")
        print(f"📊 Starte Benchmark: {benchmark_info['name']}")
        print(f"{'='*60}")
        print(f"Modell: {model}")
        print(f"Tests: {len(assets)}")
        print(f"{'='*60}\n")
        
        results = []
        
        # Progress bar
        # Use a cleaner format without the default bar to avoid clutter
        print("Fortschritt:")
        
        for i, asset_path in enumerate(assets, 1):
            asset_name = asset_path.stem.replace('asset_', '').replace('_', ' ').title()
            
            # Print status line (will be overwritten by result)
            print(f"   ⏳ [{i}/{len(assets)}] {asset_name}: Test läuft...", end="\r", flush=True)
            
            try:
                result = self._process_single_test(model, asset_path, commercial_refs, benchmark_info)
                results.append(result)
                
                quality = self._get_quality_badge(result['percentage'])
                
                # Clear line and print result
                print(" " * 80, end="\r")
                if result.get('status') == 'error':
                    error_msg = result.get('error_message', 'Incompatible Model')
                    print(
                        f"   ✗ [{i}/{len(assets)}] {asset_name}: FAILED ({error_msg}) | "
                        f"Zeit: {result['execution_time']}s"
                    )
                # Zeige Vergleich zu Referenz
                elif result['reference_score'] > 0:
                    diff = result['score_difference']
                    diff_symbol = "+" if diff > 0 else ""
                    print(
                        f"   ✓ [{i}/{len(assets)}] {asset_name}: "
                        f"{result['total_score']}/{result['max_score']} "
                        f"({result['percentage']}%) {quality} | "
                        f"Ref: {result['reference_percentage']}% | "
                        f"Diff: {diff_symbol}{diff:.1f}"
                    )
                else:
                    print(
                        f"   ✓ [{i}/{len(assets)}] {asset_name}: "
                        f"{result['total_score']}/{result['max_score']} "
                        f"({result['percentage']}%) {quality} | "
                        f"Zeit: {result['execution_time']}s"
                    )
            
            except Exception as e:
                print(" " * 80, end="\r")
                print(f"   ✗ [{i}/{len(assets)}] {asset_name}: Abgebrochen - {str(e)[:50]}...")
        
        return results
    
    # Quality thresholds (Adjusted for Hardened Assets v3.0)
    # > 90%: Expert Level (Gemini 3, Opus 4.5)
    # > 75%: Production Ready (GPT-4o, Claude 3.5)
    # > 60%: Usable / Competent (Strong Local Models)
    # < 60%: Weak / Limited
    
    QUALITY_EXCELLENT = 85  # Trophy badge (Weltklasse)
    QUALITY_GOOD = 70       # Star badge (Sehr gut / Brauchbar)
    QUALITY_OK = 55         # Checkmark badge (OK für einfache Tasks)
    
    @staticmethod
    def _get_quality_badge(percentage: float) -> str:
        """Gibt Quality-Badge zurück."""
        if percentage >= LocalBenchmarkRunner.QUALITY_EXCELLENT:
            return "🏆"
        elif percentage >= LocalBenchmarkRunner.QUALITY_GOOD:
            return "⭐"
        elif percentage >= LocalBenchmarkRunner.QUALITY_OK:
            return "✓"
        else:
            return "⚠️"
    
    def save_results(self, results: List[Dict[str, Any]]) -> None:
        """Speichert Ergebnisse in CSV via ResultManager."""
        path = self.result_manager.save_results(results, 'local')
        
        print(f"\n{'='*60}")
        if path:
            print(f"✅ Ergebnisse gespeichert: {path}")
        print(f"{'='*60}")

    def print_summary(self, results: List[Dict[str, Any]], model: str) -> None:
        """Druckt Zusammenfassung."""
        if not results:
            return
        
        # Filter successful results
        successful_results = [r for r in results if r.get('status') != 'error']
        failed_results = [r for r in results if r.get('status') == 'error']
        
        if not successful_results:
            print(f"\n{'='*60}")
            print("📈 BENCHMARK ZUSAMMENFASSUNG")
            print(f"{'='*60}")
            print(f"Modell: {model}")
            print(f"Tests durchgeführt: {len(results)}")
            print("❌ Alle Tests fehlgeschlagen!")
            return

        avg_score = sum(r['total_score'] for r in successful_results) / len(successful_results)
        avg_max = sum(r['max_score'] for r in successful_results) / len(successful_results)
        avg_percentage = sum(r['percentage'] for r in successful_results) / len(successful_results)
        avg_time = sum(r['execution_time'] for r in successful_results) / len(successful_results)
        avg_similarity = sum(r['golden_similarity'] for r in successful_results) / len(successful_results)
        
        quality = self._get_quality_badge(avg_percentage)
        
        print(f"\n{'='*60}")
        print("📈 BENCHMARK ZUSAMMENFASSUNG")
        print(f"{'='*60}")
        print(f"Modell: {model}")
        print(f"Tests durchgeführt: {len(results)} ({len(successful_results)} erfolgreich, {len(failed_results)} fehlgeschlagen)")
        print("\n📊 Durchschnittliche Scores (nur erfolgreiche Tests):")
        print(f"   Dein Modell: {avg_score:.1f}/{avg_max:.0f} ({avg_percentage:.1f}%) {quality}")
        
        # Referenz-Vergleich
        if successful_results and successful_results[0].get('reference_score', 0) > 0:
            avg_ref = sum(r.get('reference_score', 0) for r in successful_results) / len(successful_results)
            avg_ref_pct = sum(r.get('reference_percentage', 0) for r in successful_results) / len(successful_results)
            avg_diff = sum(r.get('score_difference', 0) for r in successful_results) / len(successful_results)
            
            print(f"   Kommerzielle Referenz: {avg_ref:.1f}/100 ({avg_ref_pct:.1f}%)")
            
            if avg_diff > 0:
                print(f"   🎯 Differenz: +{avg_diff:.1f} Punkte (besser als Referenz!)")
            elif avg_diff < 0:
                print(f"   📉 Differenz: {avg_diff:.1f} Punkte (Gap zur Referenz)")
            else:
                print("   ⚖️  Differenz: ±0 Punkte (auf Augenhöhe mit Referenz)")
        
        print(f"   Ausführungszeit: {avg_time:.1f}s")
        print(f"   Golden Standard Ähnlichkeit: {avg_similarity:.1f}%")
        
        # Beste und schlechteste Tests
        sorted_results = sorted(successful_results, key=lambda x: x['percentage'], reverse=True)
        
        print("\n🏆 Beste Tests:")
        for r in sorted_results[:3]:
            quality = self._get_quality_badge(r['percentage'])
            diff = r.get('score_difference', 0)
            diff_str = f" ({diff:+.1f})" if diff != 0 else ""
            print(f"   {r['asset_name'][:40]}: {r['percentage']}% {quality}{diff_str}")
        
        print("\n⚠️  Schwächste Tests:")
        for r in sorted_results[-3:]:
            quality = self._get_quality_badge(r['percentage'])
            diff = r.get('score_difference', 0)
            diff_str = f" ({diff:+.1f})" if diff != 0 else ""
            print(f"   {r['asset_name'][:40]}: {r['percentage']}% {quality}{diff_str}")
            
        if failed_results:
            print("\n❌ Fehlgeschlagene Tests:")
            for r in failed_results:
                print(f"   {r['asset_name'][:40]}: FAILED (Incompatible Model)")
        
        print(f"{'='*60}")


def main():
    """CLI Entry Point."""
    runner = LocalBenchmarkRunner()
    
    print("\n" + "="*60)
    print("🚀 LOKALE MODELLE BENCHMARK")
    print("="*60)
    
    # Schritt 1: Modell auswählen
    model = runner.select_model()
    if not model:
        sys.exit(1)
    
    # Schritt 2: Benchmark auswählen
    benchmark = runner.select_benchmark()
    if not benchmark:
        sys.exit(1)
    
    # Schritt 3: Benchmark durchführen
    try:
        results = runner.run_benchmark(model, benchmark)
        
        # Schritt 4: Ergebnisse speichern
        runner.save_results(results)
        
        # Schritt 5: Zusammenfassung
        runner.print_summary(results, model)
    
    except Exception as e:
        print(f"\n❌ Fehler beim Benchmark: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

