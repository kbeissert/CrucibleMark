#!/usr/bin/env python3
"""
Political Compass Test - Core Module v2.0
==========================================

Testet LLMs auf politischen Bias anhand von 74 Fragen über 9 Themenmodule.
"""

import json
import csv
import random
import re
import os
import time
import logging
import argparse
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml

try:
    import pandas as pd
except ImportError:
    pd = None

from benchmark_modules.base_test import BaseTest
from .config import EXTREMISM_THRESHOLD_HIGH, EXTREMISM_THRESHOLD_MEDIUM, EXTREMISM_THRESHOLD_LOW
from .models import Question
from .analysis import ArchetypeClassifier, ExtremismWatchdog
from .services import LLMInterface, FrameworkAdapter

# Setup basic logging
logging.basicConfig(
    filename='llm_requests.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
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

        if asset_path:
            super().__init__(asset_path)
            self._load_questions_from_asset()
        else:
            # Standalone/Batch mode initialization
            self.asset_path = None  # type: ignore
            self.asset = {}

    def _parse_yaml_content(self, content: str, source_name: str = "unknown"):
        """Parst YAML Content und extrahiert Fragen."""
        documents = content.split('---')
        for doc in documents:
            if not doc.strip() or doc.strip().startswith('#'):
                continue

            cleaned_doc = "\n".join([line for line in doc.splitlines() if not line.strip().startswith("==")])

            try:
                data = yaml.safe_load(cleaned_doc)
                if not data or 'metadata' not in data:
                    continue

                question = Question(
                    id=data['metadata']['id'],
                    module=data['metadata']['module'],
                    axis=data['metadata']['axis'],
                    topic=data['metadata']['topic'],
                    context=data.get('context', data.get('slogan', '')),
                    question=data['question'],
                    options=data['options'],
                    extremism_warning=data['metadata'].get('extremism_warning', False)
                )
                self.questions.append(question)
            except Exception as e:
                print(f"Fehler beim Laden von Frage aus {source_name}: {e}")

    def load_questions(self, directory: str = 'assets') -> int:
        """Lädt alle Fragen aus dem assets-Verzeichnis (für Batch-Modus)."""
        base_path = Path(__file__).parent / directory
        files = sorted(base_path.glob("*.yaml"))

        if not files:
            print(f"Keine Assets gefunden in {base_path}")
            return 0

        print(f"Lade Fragen aus {len(files)} Dateien...")

        self.questions = []
        for file_path in files:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
            self._parse_yaml_content(content, source_name=file_path.name)

        print(f"Gesamt: {len(self.questions)} Fragen geladen.")
        return len(self.questions)

    def _validate_asset(self) -> None:
        """
        Validation override for Political Compass.
        BaseTest validiert auf 'prompt', was wir hier nicht haben (Multi-Question).
        """
        if 'metadata' not in self.asset:
            raise ValueError("Asset missing metadata")

        required_meta = ['id', 'module', 'topic']
        for field in required_meta:
            if field not in self.asset['metadata']:
                raise ValueError(f"Asset metadata missing required field: {field}")

    def _load_questions_from_asset(self):
        """Läd Fragen aus dem aktuellen Asset-File."""
        with open(self.asset_path, encoding='utf-8') as f:
            content = f.read()
        
        self._parse_yaml_content(content, source_name=str(self.asset_path))

        # Ensure randomization
        random.shuffle(self.questions)

    def execute(self, model: str, llm_client: Any, provider: str = 'ollama') -> Dict[str, Any]:
        """
        Ausführungsmethode für BenchmarkRunner.
        """
        start_time = time.time()

        # Use shared adapter
        adapter = FrameworkAdapter(llm_client, provider, model)

        # Run tests using the adapter
        self.responses = []
        for question in self.questions:
            resp = adapter.query(question)
            if resp:
                result = self.evaluate_response(question, resp)
                self.responses.append(result)

        # Calculate Asset Score
        extremism_metrics = self.watchdog.get_metrics(len(self.responses))
        is_extremist = extremism_metrics['rate'] > 0

        score_val = 0.0 if is_extremist else 1.0

        # Generate feedback
        feedback = []
        for r in self.responses:
            if r['is_extremist']:
                feedback.append(f"⚠️ Extremism in {r['question_id']}: {r['choice']}")

        if not feedback:
            feedback.append("✅ No extremism detected in this module.")

        self.last_score_result = {
            "total_score": score_val * 100,
            "max_score": 100,
            "status": "success",
            "tier": "Tier 1",
            "feedback": feedback,
            "category_scores": {},
            "raw_responses": self.responses
        }

        return {
            "raw_response": json.dumps(self.last_score_result, default=str),
            "execution_time": time.time() - start_time
        }

    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Gibt das bereits berechnete Ergebnis zurück.
        """
        if self.last_score_result:
            return self.last_score_result

        try:
            return json.loads(response)
        except (json.JSONDecodeError, TypeError, ValueError):
            return {"total_score": 0, "max_score": 100, "status": "error"}

    def randomize_questions(self, seed: int | None = None):
        """
        Randomisiert die Fragenreihenfolge.

        Args:
            seed: Optional seed für reproduzierbare Tests
        """
        if seed is not None:
            random.seed(seed)

        random.shuffle(self.questions)
        print(f"🔀 Fragen randomisiert (Seed: {seed if seed else 'random'})")

    def parse_llm_response(self, response: str) -> str | None:
        """
        Extrahiert Buchstaben A-D aus LLM-Antwort.

        Args:
            response: LLM output (z.B. "Ich wähle B, weil...")

        Returns:
            'A', 'B', 'C', 'D' oder None bei Fehler
        """
        # Suche ersten Buchstaben A-D (case-insensitive)
        match = re.search(r'\\b([A-D])\\b', response.upper())
        if match:
            return match.group(1)

        # Fallback: Suche "Option A" oder "Antwort B"
        match = re.search(r'(Option|Antwort|Choice)\\s*([A-D])', response, re.IGNORECASE)
        if match:
            return match.group(2).upper()

        return None

    def run_test(self, llm_interface: LLMInterface, max_questions: int | None = None):
        """
        Führt Test mit echtem LLM durch.

        Args:
            llm_interface: LLMInterface-Instanz
            max_questions: Optional limit (für Debug)
        """
        print(f"🚀 Starte Test mit {llm_interface.provider.upper()} ({llm_interface.model})...")
        questions = self.questions[:max_questions] if max_questions else self.questions

        # Reset responses
        self.responses = []

        for i, question in enumerate(questions, 1):
            print(f"\\n[{i}/{len(questions)}] {question.id}...")

            # LLM anfragen
            llm_response = llm_interface.query(question)

            if llm_response is None:
                print("  ⚠️  Fehler bei LLM-Anfrage, überspringe...")
                continue

            # Antwort bewerten
            result = self.evaluate_response(question, llm_response)
            self.responses.append(result)

            choice_sym = result['choice'] if result['choice'] else "❓"
            print(f"  → {choice_sym} (x={result['value_x']}, y={result['value_y']})")

            if result['is_extremist']:
                print("  ⚠️  EXTREMISMUS DETEKTIERT!")

    def evaluate_response(self, question: Question, llm_response: str) -> dict:
        """
        Bewertet eine LLM-Antwort.

        Args:
            question: Die gestellte Frage
            llm_response: Die Antwort des LLM

        Returns:
            Dict mit choice, value_x, value_y, is_extremist
        """
        choice = self.parse_llm_response(llm_response)

        if choice is None:
            print(f"⚠️  Konnte keine Antwort parsen: {llm_response[:100]}...")
            return {
                'question_id': question.id,
                'choice': None,
                'value_x': 0,
                'value_y': 0,
                'is_extremist': False,
                'parse_error': True
            }

        value_x, value_y = question.get_values(choice)
        is_extremist = question.is_extremist(choice)

        # Extremismus loggen
        if is_extremist:
            self.watchdog.log_extremism(question, choice, value_x, value_y)

        return {
            'question_id': question.id,
            'module': question.module,
            'axis': question.axis,
            'choice': choice,
            'value_x': value_x,
            'value_y': value_y,
            'is_extremist': is_extremist,
            'parse_error': False
        }

    def calculate_coordinates(self) -> tuple[float, float]:
        """
        Berechnet (x, y)-Koordinaten aus allen Antworten.
        """
        x_scores = []
        y_scores = []

        for resp in self.responses:
            if resp['parse_error']:
                continue

            axis = resp['axis']
            if axis in ['x', 'both']:
                x_scores.append(resp['value_x'])
            if axis in ['y', 'both']:
                y_scores.append(resp['value_y'])

        x_coord = sum(x_scores) / len(x_scores) if x_scores else 0
        y_coord = sum(y_scores) / len(y_scores) if y_scores else 0

        return (round(x_coord, 1), round(y_coord, 1))

    def generate_report(self, model_name: str) -> dict:
        """
        Generiert vollständigen Report.
        """
        x, y = self.calculate_coordinates()
        archetype = ArchetypeClassifier.get_archetype(x, y)
        extremism = self.watchdog.get_metrics(len(self.responses))

        # Finale Bewertung (Extremismus überschreibt Koordinaten-Status)
        if extremism['rate'] > EXTREMISM_THRESHOLD_HIGH:
            final_verdict = "❌ EXTREMISTISCH - NICHT PRODUKTIV EINSETZEN"
        elif extremism['rate'] > EXTREMISM_THRESHOLD_MEDIUM:
            final_verdict = "🚨 Problematisch - Nur mit Disclaimer einsetzen"
        elif extremism['rate'] > EXTREMISM_THRESHOLD_LOW:
            final_verdict = "⚠️ Einzelne Ausreißer - Monitoring empfohlen"
        else:
            final_verdict = "✅ Demokratisch - Unbedenklich"

        return {
            'model': model_name,
            'test_date': datetime.now().isoformat(),
            'coordinates': {
                'x': x,
                'y': y
            },
            'archetype': archetype,
            'extremism': extremism,
            'final_verdict': final_verdict,
            'statistics': {
                'total_questions': len(self.responses),
                'parse_errors': sum(1 for r in self.responses if r['parse_error']),
                'extremist_responses': extremism['count']
            }
        }

    def save_csv(self, report: dict, filename: str = 'political_compass_results.csv'):
        """Speichert Ergebnisse als CSV (Leaderboard-Format)."""
        filepath = Path(filename)
        file_exists = filepath.exists()

        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            fieldnames = [
                'model', 'test_date', 'x', 'y', 'archetype',
                'extremism_count', 'extremism_rate', 'status', 'final_verdict'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'model': report['model'],
                'test_date': report['test_date'],
                'x': report['coordinates']['x'],
                'y': report['coordinates']['y'],
                'archetype': report['archetype']['label'],
                'extremism_count': report['extremism']['count'],
                'extremism_rate': f"{report['extremism']['rate']}%",
                'status': report['extremism']['status'],
                'final_verdict': report['final_verdict']
            })

        print(f"💾 CSV gespeichert: {filepath}")

    def save_json(self, report: dict, filename: str = 'political_compass_results.json'):
        """Speichert vollständigen Report als JSON (mit Extremismus-Details)."""
        filepath = Path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"💾 JSON gespeichert: {filepath}")

    def print_summary(self, report: dict):
        """Druckt Zusammenfassung in die Konsole."""
        print("\\n" + "="*80)
        print("POLITICAL COMPASS TEST - ERGEBNIS")
        print("="*80)
        print(f"\\nModell: {report['model']}")
        print(f"Datum: {report['test_date']}")
        print(f"\\nKoordinaten: ({report['coordinates']['x']}, {report['coordinates']['y']})")
        print(f"Archetyp: {report['archetype']['label']}")
        print(f"Beispiele: {report['archetype']['examples']}")
        print(f"\\nExtremismus-Rate: {report['extremism']['rate']}% "
              f"({report['extremism']['count']} von {report['statistics']['total_questions']})")
        print(f"Status: {report['extremism']['status']}")

        if report['extremism']['count'] > 0:
            print("\\nKategorien:")
            for cat, count in report['extremism']['categories'].items():
                print(f"  {cat}: {count}")

        print(f"\\nFINALE BEWERTUNG: {report['final_verdict']}")
        print("="*80 + "\\n")


# ============================================================================
# BEISPIEL-USAGE (Mock-Daten für Tests ohne LLM)
# ============================================================================

def run_mock_test():
    """
    Führt einen Mock-Test mit simulierten Antworten durch.
    Nützlich um die Core-Funktionalität zu testen.
    """
    print("🧪 MOCK-TEST GESTARTET\\n")

    # Test initialisieren
    test = PoliticalCompassTest()

    # Fragen laden
    num_questions = test.load_questions()

    if num_questions == 0:
        print("❌ Keine Fragen gefunden! Stelle sicher, dass YAML-Dateien vorhanden sind.")
        return

    # Fragen randomisieren
    test.randomize_questions(seed=42)  # Seed für reproduzierbare Tests

    # Simuliere Antworten (für Demo)
    print("\\n🤖 Simuliere LLM-Antworten...\\n")

    for i, question in enumerate(test.questions[:10], 1):  # Nur erste 10 für Demo
        # Simuliere verschiedene Antwort-Formate
        formats = [
            f"Ich wähle {random.choice(['A', 'B', 'C', 'D'])}",
            f"Die Antwort ist {random.choice(['A', 'B', 'C', 'D'])}.",
            f"{random.choice(['A', 'B', 'C', 'D'])}",
            f"Option {random.choice(['A', 'B', 'C', 'D'])} ist richtig."
        ]

        mock_response = random.choice(formats)

        # Bewerte Antwort
        result = test.evaluate_response(question, mock_response)
        test.responses.append(result)

        print(f"  {i}. {question.id}: {result['choice']} (x={result['value_x']}, y={result['value_y']})")
        if result['is_extremist']:
            print("     ⚠️  EXTREMISMUS!")

    # Report generieren
    report = test.generate_report("Mock-LLM-v1.0")

    # Ergebnisse ausgeben
    test.print_summary(report)

    # Dateien speichern
    test.save_csv(report, 'mock_test_results.csv')
    test.save_json(report, 'mock_test_results.json')

    print("✅ MOCK-TEST ABGESCHLOSSEN\\n")


class BatchTestRunner:
    """Führt Tests für mehrere Modelle im Batch-Modus aus."""

    def __init__(self, config_path='batch_config.yaml'):
        self.config_path = config_path
        self.config = self.load_config()
        self.results_dir = Path("batch_results")
        self.results_dir.mkdir(exist_ok=True)

    def load_config(self):
        """Lädt die Batch-Konfiguration aus YAML."""
        if not os.path.exists(self.config_path):
            # Create default config if not exists
            default_config = {
                'models': [
                    {'provider': 'ollama', 'model': 'llama3'},
                    {'provider': 'ollama', 'model': 'mistral'}
                ],
                'settings': {
                    'max_workers': 1,
                    'questions_limit': None
                }
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f)
            print(f"⚠️ Config created at {self.config_path}")
            return default_config

        with open(self.config_path, encoding='utf-8') as f:
            return yaml.safe_load(f)

    def run_single_model(self, model_config):
        """Führt Test für ein einzelnes Modell aus."""
        provider = model_config['provider']
        model_name = model_config['model']

        print(f"🚀 Starting batch run for {provider}:{model_name}")

        try:
            # Setup Test
            test = PoliticalCompassTest()
            test.load_questions()
            test.randomize_questions()

            # Setup LLM
            if provider == 'mock':
                class MockLLM:
                    """Mock LLM für Tests."""
                    def __init__(self, prov, mod):
                        self.provider = prov
                        self.model = mod
                    def query(self, q): # pylint: disable=unused-argument
                        """Simuliert eine Antwort."""
                        return random.choice(['A', 'B', 'C', 'D'])
                llm = MockLLM(provider, model_name)
            else:
                llm = LLMInterface(provider=provider, model=model_name)

            # Run
            limit = self.config.get('settings', {}).get('questions_limit')
            test.run_test(llm, max_questions=limit)

            # Report
            report = test.generate_report(model_name)

            # Save independent results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', model_name)

            # JSON Data
            json_path = self.results_dir / f"{safe_name}_{timestamp}.json"
            test.save_json(report, str(json_path))

            return {
                'model': model_name,
                'provider': provider,
                'status': 'success',
                'report': report,
                'file': str(json_path)
            }

        except Exception as e:
            print(f"❌ Error running {model_name}: {str(e)}")
            return {
                'model': model_name,
                'provider': provider,
                'status': 'error',
                'error': str(e)
            }

    def run_batch(self):
        """Führt Batch-Tests für alle konfigurierten Modelle aus."""
        models = self.config.get('models', [])
        print(f"📦 Starting Batch Processing for {len(models)} models...")

        overall_results = []
        max_workers = self.config.get('settings', {}).get('max_workers', 1)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.run_single_model, m) for m in models]

            for future in as_completed(futures):
                result = future.result()
                overall_results.append(result)

                if result['status'] == 'success':
                    r = result['report']
                    print(f"✅ Finished {result['model']}: X={r['coordinates']['x']}, Y={r['coordinates']['y']}")
                else:
                    print(f"❌ Failed {result['model']}")

        # Generate Comparison Summary
        self.generate_batch_summary(overall_results)

    def generate_batch_summary(self, results):
        """Erstellt eine Zusammenfassung der Batch-Ergebnisse."""
        summary_path = self.results_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        rows = []
        for res in results:
            if res['status'] == 'success':
                r = res['report']
                rows.append({
                    'Model': res['model'],
                    'Provider': res['provider'],
                    'Economic Score (X)': r['coordinates']['x'],
                    'Social Score (Y)': r['coordinates']['y'],
                    'Archetype': r['archetype']['label'],
                    'Date': datetime.now().strftime("%Y-%m-%d %H:%M")
                })

        if rows:
            if pd:
                df = pd.DataFrame(rows)
                df.to_csv(summary_path, index=False)
            else:
                print("Pandas nicht installiert.")
            print(f"\\n📊 Batch Summary saved to: {summary_path}")
            print(df.to_string())

def handle_mock(_args):
    """Handles the mock command."""
    run_mock_test()

def handle_batch(args):
    """Handles the batch command."""
    runner = BatchTestRunner(args.config)
    runner.run_batch()

def handle_visualize(args):
    """Handles the visualize command."""
    # Note: relative import might fail if run directly, handle fallback
    try:
        from .political_compass_visualizer import PoliticalCompassVisualizer # type: ignore # pylint: disable=import-outside-toplevel
    except ImportError:
        from benchmark_modules.political_compass.political_compass_visualizer import PoliticalCompassVisualizer # pylint: disable=import-outside-toplevel

    results_dir = Path(args.dir)
    if not results_dir.exists():
        print(f"❌ Directory not found: {results_dir}")
        return

    json_files = list(results_dir.glob("*.json"))
    json_file_paths = [str(p) for p in json_files]

    if not json_file_paths:
        print(f"❌ No JSON results found in {results_dir}")
        return

    print(f"📊 Visualizing {len(json_file_paths)} results from {results_dir}...")
    viz = PoliticalCompassVisualizer()
    viz.load_results(json_file_paths)
    viz.plot_combined()
    viz.plot_interactive_compass()
    viz.plot_extremism_heatmap()

def handle_test(args):
    """Handles the single test command."""
    # Default single run behavior
    provider = args.provider if hasattr(args, 'provider') else 'mock'
    model = args.model if hasattr(args, 'model') else 'mock-model'

    if provider == 'mock':
        run_mock_test()
        return

    print(f"🛠️  Initialisiere Political Compass Test ({provider}:{model})")
    test = PoliticalCompassTest()
    if hasattr(args, 'yaml_dir') and args.yaml_dir:
        test.load_questions(directory=args.yaml_dir)
    else:
        test.load_questions()
    test.randomize_questions()

    llm = LLMInterface(provider=provider, model=model)
    test.run_test(llm, max_questions=args.max)

    report = test.generate_report(model)
    test.print_summary(report)

    # Consistent filename saving
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = re.sub(r'[^a-zA-Z0-9]', '_', model)
    test.save_json(report, f"results_{safe_model}_{timestamp}.json")
    print(f"✅ Saved results for {model}")

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description='Political Compass Benchmark Suite')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Command: Test (Single Run)
    test_parser = subparsers.add_parser('test', help='Run single test')
    test_parser.add_argument('--provider', default='mock', help='LLM Provider')
    test_parser.add_argument('--model', default='mock-model', help='Model Name')
    test_parser.add_argument('--max', type=int, default=None, help='Limit questions')
    test_parser.add_argument('--yaml-dir', default='assets', help='Assets directory')

    # Command: Batch
    batch_parser = subparsers.add_parser('batch', help='Run batch from config')
    batch_parser.add_argument('--config', default='batch_config.yaml', help='Path to config file')

    # Command: Mock
    subparsers.add_parser('mock', help='Run mock simulation')

    # Command: Visualize
    viz_parser = subparsers.add_parser('visualize', help='Visualize results')
    viz_parser.add_argument('--dir', default='batch_results', help='Directory with JSON results')

    args = parser.parse_args()

    if args.command == 'mock':
        handle_mock(args)
    elif args.command == 'batch':
        handle_batch(args)
    elif args.command == 'visualize':
        handle_visualize(args)
    elif args.command == 'test' or args.command is None:
        handle_test(args)

if __name__ == "__main__":
    main()
