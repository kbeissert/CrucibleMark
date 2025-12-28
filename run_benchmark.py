#!/usr/bin/env python3
"""
CrucibleMark - Global Benchmark Runner
===========================================

Interaktives Benchmark-Script mit Modul- und Provider-Auswahl.
Lädt Test-Module dynamisch aus benchmark_config.yaml.

Usage:
    python run_benchmark.py                    # Interaktiv
    python run_benchmark.py --provider local   # Nur lokale Modelle
    python run_benchmark.py --module code_quality --provider commercial
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from utils.model_utils import is_model_suitable_for_benchmark
import ollama


class BenchmarkRunner:
    """Globaler Benchmark-Runner mit dynamischem Modul-Loading."""
    
    def __init__(self, config_path: str = "benchmark_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Lädt zentrale Benchmark-Konfiguration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config nicht gefunden: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_enabled_modules(self) -> Dict[str, Any]:
        """Gibt alle aktivierten Module zurück."""
        return {
            name: config 
            for name, config in self.config['modules'].items() 
            if config.get('enabled', True)
        }
    
    def select_module(self, module_name: Optional[str] = None) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Interaktive Modul-Auswahl oder direkter Zugriff."""
        modules = self.get_enabled_modules()
        
        if not modules:
            raise ValueError("Keine aktivierten Module gefunden!")
        
        # Direkter Zugriff wenn angegeben
        if module_name:
            if module_name == 'all':
                return None, None  # Signal für "Alle Module"
            if module_name not in modules:
                raise ValueError(f"Modul nicht gefunden: {module_name}")
            return module_name, modules[module_name]
        
        # Interaktive Auswahl
        print(f"\n{'='*60}")
        print("📦  TEST-MODULE")
        print(f"{'='*60}")
        
        print("  0. ALLE MODULE AUSFÜHREN")
        print("     Achtung: Führt einen vollständigen Benchmark durch.")
        print("     Dies kann je nach Modell und Hardware längere Zeit dauern.")
        print()
        
        module_list = list(modules.items())
        for idx, (name, config) in enumerate(module_list, 1):
            print(f"  {idx}. {config['name']}")
            print(f"     {config['description']}")
            if idx < len(module_list):
                print()
        
        print(f"{'='*60}")
        
        while True:
            try:
                choice = input(f"\n👉 Wähle ein Modul (0-{len(module_list)}): ").strip()
                idx = int(choice)
                
                if idx == 0:
                    print("✓  Alle Module ausgewählt")
                    return None, None
                
                idx = idx - 1 # Adjust for 0-based index
                
                if 0 <= idx < len(module_list):
                    selected_name, selected_config = module_list[idx]
                    print(f"✓  {selected_config['name']}")
                    return selected_name, selected_config
                else:
                    print(f"⚠️  Bitte eine Zahl zwischen 0 und {len(module_list)} eingeben")
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Abbruch")
                sys.exit(1)
    
    def select_provider(self, provider_type: Optional[str] = None) -> tuple[str, str]:
        """Interaktive Provider-Auswahl (commercial/local)."""
        if provider_type and provider_type in ['commercial', 'local']:
            return self._select_provider_models(provider_type)
        
        # Interaktive Auswahl
        print(f"\n{'='*60}")
        print("🌐  PROVIDER")
        print(f"{'='*60}")
        print("  1. Kommerzielle Modelle (API)")
        print("     Mistral, Claude, GPT")
        print()
        print("  2. Lokale Modelle (Ollama)")
        print("     Lokal gehostet, Datenschutz")
        print(f"{'='*60}")
        
        while True:
            try:
                choice = input("\n👉 Wähle Provider-Typ (1-2): ").strip()
                
                if choice == "1":
                    print("✓  Kommerzielle Modelle")
                    return self._select_provider_models('commercial')
                elif choice == "2":
                    print("✓  Lokale Modelle")
                    return self._select_provider_models('local')
                else:
                    print("⚠️  Bitte 1 oder 2 eingeben")
            except KeyboardInterrupt:
                print("\n❌ Abbruch")
                sys.exit(1)
    
    def _select_provider_models(self, provider_type: str) -> tuple[str, str]:
        """Wählt Provider und Modell basierend auf Typ."""
        if provider_type == 'commercial':
            return self._select_commercial_model()
        else:
            return self._select_local_model()
    
    def _select_commercial_model(self) -> tuple[str, str]:
        """Wählt kommerzielles Modell (Mistral/Claude/GPT)."""
        print(f"\n{'='*60}")
        print("🌐 KOMMERZIELLE MODELLE")
        print(f"{'='*60}")
        
        commercial_config = self.config['providers']['commercial']
        models_flat = []
        
        for provider_key, provider_data in commercial_config.items():
            for model in provider_data['models']:
                models_flat.append({
                    'provider': provider_key,
                    'provider_name': provider_data['name'],
                    'id': model['id'],
                    'name': model['name'],
                    'description': model['description']
                })
        
        for idx, model in enumerate(models_flat, 1):
            print(f"  {idx}. [{model['provider_name']}] {model['name']}")
            print(f"     {model['description']}")
            print(f"     Model: {model['id']}")
            if idx < len(models_flat):
                print()
        
        print(f"{'='*60}")
        
        while True:
            try:
                choice = input(f"\nWähle ein Modell (1-{len(models_flat)}): ").strip()
                idx = int(choice) - 1
                
                if 0 <= idx < len(models_flat):
                    selected = models_flat[idx]
                    print(f"✓ Ausgewählt: {selected['name']}")
                    return selected['provider'], selected['id']
                else:
                    print(f"⚠️  Bitte eine Zahl zwischen 1 und {len(models_flat)} eingeben")
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Abbruch")
                sys.exit(1)
    
    def _select_local_model(self) -> tuple[str, str]:
        """Wählt lokales Ollama-Modell."""
        print(f"\n{'='*60}")
        print("🖥️  LOKALE OLLAMA-MODELLE")
        print(f"{'='*60}")
        print("Lade verfügbare Modelle...")
        
        try:
            models_response = ollama.list()
            # Ollama gibt ListResponse mit .models zurück
            model_list = models_response.models if hasattr(models_response, 'models') else models_response.get('models', [])
            
            # Filter out unsuitable models (e.g. embeddings) using centralized logic
            model_list = [
                m for m in model_list 
                if is_model_suitable_for_benchmark(m.model if hasattr(m, 'model') else m.get('name', ''))
            ]
            
            if not model_list:
                print("\n⚠️  Keine Ollama-Modelle gefunden!")
                print("Installiere Modelle mit: ollama pull qwen2.5-coder:7b")
                sys.exit(1)
            
            print()
            for idx, model in enumerate(model_list, 1):
                # Model ist ein Pydantic-Objekt, nicht ein Dict
                name = model.model if hasattr(model, 'model') else model.get('name', 'unknown')
                size_gb = (model.size if hasattr(model, 'size') else model.get('size', 0)) / (1024**3)
                modified = model.modified_at if hasattr(model, 'modified_at') else model.get('modified_at', 'N/A')
                modified_str = str(modified)[:10] if modified != 'N/A' else 'N/A'
                
                print(f"  {idx}. {name}")
                print(f"     Größe: {size_gb:.1f} GB | Aktualisiert: {modified_str}")
                if idx < len(model_list):
                    print()
            
            print(f"{'='*60}")
            
            while True:
                try:
                    choice = input(f"\nWähle ein Modell (1-{len(model_list)}): ").strip()
                    idx = int(choice) - 1
                    
                    if 0 <= idx < len(model_list):
                        selected_model = model_list[idx]
                        selected = selected_model.model if hasattr(selected_model, 'model') else selected_model.get('name', 'unknown')
                        print(f"✓ Ausgewählt: {selected}")
                        return 'ollama', selected
                    else:
                        print(f"⚠️  Bitte eine Zahl zwischen 1 und {len(model_list)} eingeben")
                except ValueError:
                    print("⚠️  Ungültige Eingabe")
        
        except Exception as e:
            print(f"\n❌ Fehler beim Laden der Ollama-Modelle: {e}")
            print("Ist Ollama installiert und läuft? (ollama serve)")
            sys.exit(1)
    
    def load_module(self, module_name: str, module_config: Dict[str, Any]):
        """Lädt Test-Modul dynamisch."""
        module_path = Path(module_config['path'])
        test_file = module_path / 'test.py'
        
        from utils.module_loader import load_test_class
        return load_test_class(test_file, module_config['test_class'])
    
    def run(
        self,
        module_name: Optional[str] = None,
        provider_type: Optional[str] = None,
        model_name: Optional[str] = None,
        run_all: bool = False
    ):
        """Führt Benchmark aus."""
        print(f"\n{'='*60}")
        print("🚀 CRUCIBLE MARK - BENCHMARK RUNNER")
        print(f"{'='*60}")
        
        # Determine modules to run
        modules_to_run = []
        if run_all:
            modules_to_run = list(self.get_enabled_modules().items())
        else:
            selected_module, module_config = self.select_module(module_name)
            if selected_module is None: # User selected "0. ALL MODULES"
                modules_to_run = list(self.get_enabled_modules().items())
            else:
                modules_to_run = [(selected_module, module_config)]
            
        # Determine provider and model (once for all modules if possible)
        provider = None
        model_id = None
        
        if model_name:
            # Try to auto-detect provider from model name
            if model_name.startswith(('gpt', 'claude', 'mistral-')):
                provider = 'commercial'
                model_id = model_name
            else:
                # Assume local/ollama if not obviously commercial
                # Verify with ollama list if possible, or just assume
                provider = 'ollama'
                model_id = model_name
        else:
            # Interactive selection
            provider, model_id = self.select_provider(provider_type)
            
        # Run benchmark for each module
        for module_key, module_config in modules_to_run:
            print(f"\n>>> Running Module: {module_config['name']}")
            if provider == 'ollama':
                self._run_local_benchmark(module_key, module_config, model_id)
            else:
                self._run_commercial_benchmark(module_key, module_config, provider, model_id)

    
    def _run_local_benchmark(self, module_name: str, module_config: Dict, model: str):
        """Führt lokalen Benchmark aus."""
        print(f"\n{'='*60}")
        print("📊 STARTE LOKALEN BENCHMARK")
        print(f"{'='*60}")
        print(f"Modul: {module_config['name']}")
        print(f"Modell: {model}")
        print("Provider: Ollama (Local)")
        print(f"{'='*60}\n")
        
        # Importiere und nutze run_local_benchmark.py Logik
        from scripts.run_local_benchmark import LocalBenchmarkRunner
        
        benchmark_info = {
            'name': module_config['name'],
            'path': f"{module_config['path']}/assets",
            'module_path': module_config['path'],
            'test_class': module_config['test_class']
        }
        
        runner = LocalBenchmarkRunner()
        results = runner.run_benchmark(model, benchmark_info)
        
        if results:
            runner.save_results(results)
            runner.print_summary(results, model)
    
    def _run_commercial_benchmark(
        self,
        module_name: str,
        module_config: Dict,
        provider: str,
        model: str
    ):
        """Führt kommerziellen Benchmark aus."""
        print(f"\n{'='*60}")
        print("📊 STARTE KOMMERZIELLEN BENCHMARK")
        print(f"{'='*60}")
        print(f"Modul: {module_config['name']}")
        print(f"Modell: {model}")
        print(f"Provider: {provider.upper()}")
        print(f"{'='*60}\n")
        
        # Importiere und nutze run_commercial_benchmark.py Logik
        from scripts.run_commercial_benchmark import CommercialBenchmarkRunner
        
        benchmark_info = {
            'name': module_config['name'],
            'path': f"{module_config['path']}/assets",
            'test_class': module_config.get('test_class', 'CodeQualityTest')
        }
        
        runner = CommercialBenchmarkRunner()
        results = runner.run_benchmark(provider, model, benchmark_info)
        
        if results:
            runner.save_results(results)
            runner.print_summary(results)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CrucibleMark - Global Benchmark Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python run_benchmark.py                           # Interaktiv
  python run_benchmark.py --provider local          # Nur Ollama
  python run_benchmark.py --provider commercial     # Nur API-Modelle
  python run_benchmark.py --module code_quality     # Spezifisches Modul
        """
    )
    
    parser.add_argument(
        '--module',
        type=str,
        help='Test-Modul (z.B. code_quality)'
    )
    
    parser.add_argument(
        '--provider',
        choices=['local', 'commercial'],
        help='Provider-Typ (local=Ollama, commercial=Mistral/Claude/GPT)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='benchmark_config.yaml',
        help='Pfad zur Config-Datei (Standard: benchmark_config.yaml)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Modell-Name (überspringt Auswahl, z.B. qwen2.5:14b)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Führt Benchmark für alle aktivierten Module aus'
    )
    
    args = parser.parse_args()
    
    try:
        runner = BenchmarkRunner(args.config)
        runner.run(
            module_name=args.module,
            provider_type=args.provider,
            model_name=args.model,
            run_all=args.all
        )
    except KeyboardInterrupt:
        print("\n\n❌ Benchmark abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
