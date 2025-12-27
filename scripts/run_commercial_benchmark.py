#!/usr/bin/env python3
"""Benchmark Runner für kommerzielle API-basierte Modelle.

Zwei Modi:
1. Golden Standard Mode: Generiert golden_standard_benchmark.csv
2. Test Mode: Testet beliebige Modelle → commercial_models_benchmark.csv
"""

import json
import sys
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import yaml
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.llm_client import LLMClient
from utils.config_validator import ConfigValidator
from utils.module_loader import load_test_class


class CommercialBenchmarkRunner:
    """Benchmark Runner für kommerzielle API-basierte Modelle."""
    
    BENCHMARK_CATEGORIES = {
        'code_quality': {
            'name': 'Code Quality',
            'description': 'WCAG, Security, Performance, API Design, Code Smells',
            'path': 'test_modules/code_quality/assets'
        }
    }
    
    def __init__(self, mode: str = 'test'):
        """Initialisiert Runner.
        
        Args:
            mode: 'golden_standard' oder 'test'
                  - golden_standard: Nur das Golden Standard Modell
                  - test: Beliebige kommerzielle Modelle
        """
        self.client = LLMClient()
        self.validator = ConfigValidator()
        self.mode = mode
        
        # CSV-Datei je nach Modus
        if mode == 'golden_standard':
            self.results_csv = self.validator.get_golden_standard_csv()
        else:
            # Aus Config laden
            config = self.validator.config
            csv_file = config.get('output', {}).get('commercial_csv', 'commercial_models_benchmark.csv')
            self.results_csv = Path(csv_file)
    
    def get_available_providers(self) -> Dict[str, Dict]:
        """Holt aktivierte kommerzielle Provider aus Config.
        
        Returns:
            Dict mit provider_key -> provider_config (nur enabled=true)
        """
        return self.validator.get_enabled_commercial_providers()
    
    def select_mode(self) -> Optional[str]:
        """Wähle Benchmark-Modus."""
        print(f"\n{'='*60}")
        print("🎯 BENCHMARK-MODUS")
        print(f"{'='*60}")
        print("  1. Golden Standard generieren")
        print("     → Erstellt Referenz-Benchmark für lokale Vergleiche")
        print(f"     → Speichert in: {self.validator.get_golden_standard_csv()}")
        print()
        print("  2. Kommerzielle Modelle testen")
        print("     → Testet beliebige kommerzielle LLMs")
        print(f"     → Speichert in: commercial_models_benchmark.csv")
        print(f"{'='*60}")
        
        while True:
            try:
                choice = input("\nWähle Modus (1-2): ").strip()
                
                if choice == '1':
                    print("✓ Golden Standard Mode\n")
                    return 'golden_standard'
                elif choice == '2':
                    print("✓ Test Mode\n")
                    return 'test'
                else:
                    print("❌ Bitte 1 oder 2 eingeben")
            
            except KeyboardInterrupt:
                print("\n\n❌ Abgebrochen")
                return None
    
    def select_golden_standard_model(self) -> Optional[Tuple[str, str]]:
        """Holt das Golden Standard Modell aus Config.
        
        Returns:
            (provider, model_id) oder None
        """
        info = self.validator.get_golden_standard_info()
        if not info:
            print("❌ Kein Golden Standard in Config definiert")
            return None
        
        provider_key, model_id, provider_config = info
        provider_name = provider_config.get('name', provider_key)
        
        # Modell-Details
        models = provider_config.get('models', [])
        model_config = next((m for m in models if m.get('id') == model_id), {})
        model_name = model_config.get('name', model_id)
        
        print(f"\n{'='*60}")
        print("🏆 GOLDEN STANDARD MODELL")
        print(f"{'='*60}")
        print(f"Provider: {provider_name}")
        print(f"Modell: {model_name}")
        print(f"ID: {model_id}")
        print(f"{'='*60}\n")
        
        return (provider_key, model_id)
    
    def select_test_model(self) -> Optional[Tuple[str, str]]:
        """Interaktive Modell-Auswahl für Test Mode.
        
        Returns:
            (provider, model_id) oder None
        """
        providers = self.get_available_providers()
        
        print(f"\n{'='*60}")
        print("🌐 VERFÜGBARE MODELLE")
        print(f"{'='*60}")
        
        # Flatten models
        model_list = []
        for provider_key, provider_config in providers.items():
            provider_name = provider_config.get('name', provider_key)
            models = provider_config.get('models', [])
            
            for model in models:
                model_id = model.get('id')
                model_name = model.get('name', model_id)
                description = model.get('description', '')
                model_list.append((provider_key, model_id, provider_name, model_name, description))
        
        for i, (provider_key, model_id, provider_name, model_name, description) in enumerate(model_list, 1):
            print(f"  {i}. [{provider_name}] {model_name}")
            if description:
                print(f"     {description}")
            print(f"     ID: {model_id}")
            print()
        
        print(f"{'='*60}")
        
        while True:
            try:
                choice = input(f"\nWähle Modell (1-{len(model_list)}): ").strip()
                
                if not choice:
                    print("❌ Keine Eingabe - Abbruch")
                    return None
                
                idx = int(choice) - 1
                
                if 0 <= idx < len(model_list):
                    provider_key, model_id, provider_name, model_name, _ = model_list[idx]
                    print(f"✓ Ausgewählt: {provider_name} - {model_name}\n")
                    return (provider_key, model_id)
                else:
                    print(f"❌ Bitte Zahl zwischen 1 und {len(model_list)} eingeben")
            
            except ValueError:
                print("❌ Ungültige Eingabe - bitte Zahl eingeben")
            except KeyboardInterrupt:
                print("\n\n❌ Abgebrochen")
                return None
    
    def select_benchmark(self) -> Optional[Dict[str, Any]]:
        """Interaktive Benchmark-Auswahl."""
        print(f"\n{'='*60}")
        print("📊 VERFÜGBARE BENCHMARKS")
        print(f"{'='*60}")
        
        categories = list(self.BENCHMARK_CATEGORIES.items())
        
        for i, (key, info) in enumerate(categories, 1):
            print(f"  {i}. {info['name']}")
            print(f"     {info['description']}")
            print()
        
        print(f"{'='*60}")
        
        while True:
            try:
                choice = input(f"\nWähle Benchmark (1-{len(categories)}): ").strip()
                
                if not choice:
                    print("❌ Keine Eingabe - Abbruch")
                    return None
                
                idx = int(choice) - 1
                
                if 0 <= idx < len(categories):
                    key, info = categories[idx]
                    print(f"✓ Ausgewählt: {info['name']}\n")
                    return info
                else:
                    print(f"❌ Bitte Zahl zwischen 1 und {len(categories)} eingeben")
            
            except ValueError:
                print("❌ Ungültige Eingabe - bitte Zahl eingeben")
            except KeyboardInterrupt:
                print("\n\n❌ Abgebrochen")
                return None

    def discover_assets(self, assets_path: str) -> List[Path]:
        """Findet alle YAML-Assets im Verzeichnis."""
        path = Path(assets_path)
        if not path.exists():
            return []
        return sorted(list(path.glob('asset_*.yaml')))

    def _get_quality_badge(self, percentage: float) -> str:
        """Gibt Qualitäts-Badge zurück."""
        if percentage >= 90: return "🌟 EXCELLENT"
        if percentage >= 80: return "✅ GOOD"
        if percentage >= 70: return "⚠️  OK"
        if percentage >= 50: return "📉 WEAK"
        return "❌ FAIL"

    def run_benchmark(
        self,
        provider: str,
        model: str,
        benchmark_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Führt Benchmark für gewähltes Modell durch.
        
        Args:
            provider: Provider Name (mistral, anthropic, openai)
            model: Modell ID
            benchmark_info: Benchmark Konfiguration
            
        Returns:
            Liste mit Testergebnissen
        """
        print(f"\n{'='*60}")
        print(f"📊 STARTE BENCHMARK: {benchmark_info['name']}")
        print(f"{'='*60}")
        print(f"Provider: {provider}")
        print(f"Modell: {model}")
        print(f"Modus: {self.mode}")
        print(f"{'='*60}\n")
        
        # Discover assets
        assets = self.discover_assets(benchmark_info['path'])
        print(f"Gefundene Tests: {len(assets)}\n")
        
        results = []
        
        for asset_path in assets:
            try:
                # Load asset
                with open(asset_path, 'r', encoding='utf-8') as f:
                    asset_data = yaml.safe_load(f)
                
                print(f"▶️  Teste: {asset_data['metadata']['name']}...")
                
                # Load Test Class
                module_path = Path(benchmark_info['path']).parent / 'test.py'
                test_class_name = benchmark_info.get('test_class', 'CodeQualityTest')
                
                try:
                    TestClass = load_test_class(module_path, test_class_name)
                except (FileNotFoundError, ImportError, AttributeError) as e:
                     print(f"❌ Fehler beim Laden des Test-Moduls: {e}")
                     continue
                
                test = TestClass(asset_path)
                
                # Execute
                # Pass provider to execute method
                exec_result = test.execute(model, self.client, provider=provider)
                response = exec_result['raw_response']
                execution_time = exec_result['execution_time']
                
                # Score
                score = test.score_response(response)
                
                # Result Object
                result = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': score.get('status', 'success'),
                    'provider': provider,
                    'model': model,
                    'asset_id': asset_data['metadata']['id'],
                    'asset_name': asset_data['metadata']['name'],
                    'total_score': score['total_score'],
                    'max_score': score['max_score'],
                    'percentage': round((score['total_score'] / score['max_score'] * 100), 1),
                    'execution_time': round(execution_time, 1),
                    'response_length': len(response)
                }
                
                # Add category scores
                for cat_name, cat_data in score['category_scores'].items():
                    result[f'{cat_name}'] = f"{cat_data['achieved']}/{cat_data['max']}"
                
                results.append(result)
                
                # Print immediate result
                badge = self._get_quality_badge(result['percentage'])
                print(f"   Ergebnis: {result['percentage']}% {badge} ({result['total_score']}/{result['max_score']} Pkt)")
                
                # Save Golden Standard JSON if in correct mode
                if self.mode == 'golden_standard':
                    self._save_golden_json(provider, asset_data['metadata']['id'], response)
                
            except Exception as e:
                print(f"❌ Fehler bei {asset_path.name}: {e}")
                import traceback
                traceback.print_exc()
        
        return results

    def _save_golden_json(self, provider: str, asset_id: str, response: str) -> None:
        """Speichert die volle Antwort als JSON für Similarity-Checks."""
        output_dir = Path(f"golden_standards/{provider}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{asset_id}.json"
        
        data = {
            "id": asset_id,
            "provider": provider,
            "timestamp": datetime.now().isoformat(),
            "response": response
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"   💾 Golden Standard JSON gespeichert: {output_file}")
        except Exception as e:
            print(f"   ⚠️  Fehler beim Speichern des Golden Standard JSON: {e}")

    def save_results(self, results: List[Dict[str, Any]]) -> None:
        """Speichert Ergebnisse in CSV."""
        if not results:
            return
            
        file_exists = self.results_csv.exists()
        fieldnames = list(results[0].keys())
        
        try:
            with open(self.results_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(results)
            print(f"\n💾 Ergebnisse gespeichert in: {self.results_csv}")
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")

    def print_summary(self, results: List[Dict[str, Any]]) -> None:
        """Druckt Zusammenfassung."""
        if not results:
            return
            
        print(f"\n{'='*60}")
        print("📊 ZUSAMMENFASSUNG")
        print(f"{'='*60}")
        
        total_score = sum(r['total_score'] for r in results)
        max_possible = sum(r['max_score'] for r in results)
        avg_percentage = (total_score / max_possible * 100) if max_possible > 0 else 0
        
        print(f"Gesamt-Score: {total_score:.1f}/{max_possible} ({avg_percentage:.1f}%)")
        print(f"Qualität: {self._get_quality_badge(avg_percentage)}")
        print(f"{'-'*60}")
        
        for r in results:
            badge = self._get_quality_badge(r['percentage'])
            print(f"{r['asset_name'][:40]:<40} | {r['percentage']:>5.1f}% | {badge}")
        
        print(f"{'='*60}\n")



def main():
    """Hauptfunktion."""
    print("\n" + "="*60)
    print("🚀 KOMMERZIELLE MODELLE BENCHMARK")
    print("="*60)
    
    # Runner ohne Modus initialisieren
    runner = CommercialBenchmarkRunner()
    
    # 1. Modus wählen
    mode = runner.select_mode()
    if not mode:
        return
    
    # Runner mit gewähltem Modus neu initialisieren
    runner = CommercialBenchmarkRunner(mode=mode)
    
    # 2. Modell wählen (je nach Modus)
    if mode == 'golden_standard':
        # Golden Standard aus Config
        result = runner.select_golden_standard_model()
    else:
        # Beliebiges Modell
        result = runner.select_test_model()
    
    if not result:
        return
    
    provider, model_id = result
    
    # 3. Benchmark wählen
    benchmark_info = runner.select_benchmark()
    if not benchmark_info:
        return
    
    print(f"\n{'='*60}")
    print(f"📊 STARTE BENCHMARK")
    print(f"{'='*60}")
    print(f"Modus: {'🏆 Golden Standard' if mode == 'golden_standard' else '🧪 Test'}")
    print(f"Provider: {provider}")
    print(f"Modell: {model_id}")
    print(f"Benchmark: {benchmark_info['name']}")
    print(f"Ergebnis: {runner.results_csv}")
    print(f"{'='*60}\n")
    
    print("⚠️  Implementierung noch ausstehend - Struktur steht!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Abgebrochen durch Benutzer")
        sys.exit(1)
