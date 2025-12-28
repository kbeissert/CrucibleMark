"""
Base Test Class für LLM Benchmark Suite
Abstract Base Class für alle Test-Module
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, NamedTuple
import yaml
import json
from datetime import datetime


# Scoring constant
TOTAL_SCORING_WEIGHT = 100


class BenchmarkResultData(NamedTuple):
    """Container für Test-Ergebnisdaten."""
    model: str
    response: str
    score: Dict[str, Any]
    comparison: Dict[str, Any]
    output_dir: Path
    output_file: Optional[Path] = None


class BaseTest(ABC):
    """
    Abstract Base Class für alle Benchmark-Tests
    
    Funktionalität:
    - Lädt YAML-Test-Assets
    - Validiert Asset-Schema
    - Definiert Interface für konkrete Tests
    - Vergleicht Responses mit Golden Standards
    - Speichert Ergebnisse als Markdown + JSON
    """
    
    def __init__(self, asset_path: Path):
        """
        Initialisiert den Test mit einem Asset
        
        Args:
            asset_path: Pfad zur YAML-Test-Asset-Datei
        """
        self.asset_path = Path(asset_path)
        self.asset = self._load_asset()
        self._validate_asset()
        
    def _load_asset(self) -> Dict[str, Any]:
        """
        Lädt YAML-Test-Asset
        
        Returns:
            Dict mit Asset-Daten
        """
        with open(self.asset_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _validate_asset(self) -> None:
        """
        Validiert Asset-Schema
        
        Raises:
            ValueError: Wenn erforderliche Felder fehlen
        """
        required_fields = ['metadata', 'prompt', 'scoring']
        
        for field in required_fields:
            if field not in self.asset:
                raise ValueError(f"Asset missing required field: {field}")
        
        # Validiere Scoring-Gewichte
        if 'scoring' in self.asset:
            total_weight = sum(
                cat.get('weight', 0) 
                for cat in self.asset['scoring'].values()
                if isinstance(cat, dict)
            )
            if total_weight != TOTAL_SCORING_WEIGHT:
                raise ValueError(f"Scoring weights must sum to {TOTAL_SCORING_WEIGHT}, got {total_weight}")
    
    @abstractmethod
    def execute(self, model: str, llm_client) -> Dict[str, Any]:
        """
        Führt Test aus und gibt Response zurück
        
        Args:
            model: Name des zu testenden Modells
            llm_client: LLM Client Instanz
            
        Returns:
            Dict mit Response-Daten:
            {
                'response': str,
                'execution_time': float,
                'metadata': dict
            }
        """
        pass
    
    @abstractmethod
    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Bewertet Response nach Asset-Kriterien
        
        Args:
            response: LLM Response Text
            
        Returns:
            Dict mit Scoring-Ergebnissen:
            {
                'total_score': int,
                'category_scores': {
                    'category_name': {
                        'achieved': int,
                        'max': int,
                        'details': str
                    }
                }
            }
        """
        pass
    
    def compare_to_golden_standard(self, response: str, golden_path: Path) -> Dict[str, Any]:
        """
        Vergleicht Response mit Golden Standard
        
        Args:
            response: LLM Response
            golden_path: Pfad zum Golden Standard JSON
            
        Returns:
            Dict mit Vergleichs-Metriken
        """
        if not golden_path.exists():
            return {
                'status': 'no_golden_standard',
                'message': 'No golden standard available for comparison'
            }
        
        with open(golden_path, 'r', encoding='utf-8') as f:
            golden_data = json.load(f)
        
        golden_response = golden_data.get('response', '')
        
        # Einfache Textähnlichkeit (kann später durch Embeddings ersetzt werden)
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, response, golden_response).ratio()
        
        return {
            'status': 'compared',
            'similarity': similarity,
            'golden_model': golden_data.get('model', 'unknown'),
            'length_ratio': len(response) / max(len(golden_response), 1)
        }
    
    def save_result(
        self, 
        result_data: BenchmarkResultData
    ) -> None:
        """
        Speichert Ergebnisse als Markdown + JSON
        
        Args:
            result_data: BenchmarkResultData container mit allen benötigten Daten
        """
        output_dir = Path(result_data.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize model name für Dateinamen
        safe_model_name = result_data.model.replace(':', '_').replace('/', '_')
        asset_id = self.asset['metadata']['id']
        
        # Determine base filename
        if result_data.output_file:
            base_name = result_data.output_file.stem
        else:
            base_name = f"{asset_id}_{safe_model_name}"
        
        # Markdown Report
        md_path = output_dir / f"{base_name}.md"
        self._write_markdown_report(
            md_path, 
            result_data.model, 
            result_data.response, 
            result_data.score, 
            result_data.comparison
        )
        
        # JSON Result
        json_path = output_dir / f"{base_name}.json"
        self._write_json_result(
            json_path, 
            result_data.model, 
            result_data.response, 
            result_data.score, 
            result_data.comparison
        )
    
    def _write_markdown_report(
        self,
        path: Path,
        model: str,
        response: str,
        score: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> None:
        """Schreibt Markdown Report"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# {self.asset['metadata']['name']}\n\n")
            f.write(f"**Modell:** {model}\n\n")
            f.write(f"**Kategorie:** {self.asset['metadata']['category']}\n\n")
            f.write(f"**Timestamp:** {datetime.now().isoformat()}\n\n")
            
            f.write("## Score\n\n")
            f.write(f"**Total:** {score['total_score']}/100\n\n")
            
            f.write("### Kategorien\n\n")
            for cat_name, cat_data in score['category_scores'].items():
                f.write(f"- **{cat_name}:** {cat_data['achieved']}/{cat_data['max']}\n")
                if 'details' in cat_data:
                    f.write(f"  - {cat_data['details']}\n")
            
            if comparison['status'] == 'compared':
                f.write("\n## Golden Standard Vergleich\n\n")
                f.write(f"- **Similarity:** {comparison['similarity']:.2%}\n")
                f.write(f"- **Reference Model:** {comparison['golden_model']}\n")
                f.write(f"- **Length Ratio:** {comparison['length_ratio']:.2f}\n")
            
            f.write("\n## Response\n\n")
            f.write("```\n")
            f.write(response)
            f.write("\n```\n")
    
    def _write_json_result(
        self,
        path: Path,
        model: str,
        response: str,
        score: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> None:
        """Schreibt JSON Result"""
        result = {
            'metadata': self.asset['metadata'],
            'model': model,
            'timestamp': datetime.now().isoformat(),
            'response': response,
            'score': score,
            'comparison': comparison
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
