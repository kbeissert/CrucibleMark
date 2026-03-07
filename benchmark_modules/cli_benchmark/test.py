import json
import time
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List

from schemas.result import BenchmarkResult
from benchmark_modules.cli_benchmark.core.tasks import CLITaskLoader
from benchmark_modules.cli_benchmark.core.evaluator import CLIEvaluator
from benchmark_modules.cli_benchmark.core.constants import (
    CLI_GOLD_THRESHOLD, 
    CLI_SILVER_THRESHOLD, 
    CLI_BRONZE_THRESHOLD, 
    SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)

class CLIBenchmarkTest:
    """
    Test-Klasse für CLI Benchmark. Führt Shell-Simulations-Aufgaben aus.
    Batch Mode.
    """
    
    def __init__(self):
        self.loader = CLITaskLoader()
        self.evaluator = CLIEvaluator()
        self.questions = []
        self.num_runs = 1
        self.config = {}
        self.generation_config = {"temperature": 0.1} # fallback
        self._load_module_config()

    def _load_module_config(self):
        """Loads execution and generation parameters from config.yaml."""
        try:
            config_path = Path(__file__).parent / "config.yaml"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    self.config = data.get("config", {})
                    
                    # Override defaults with generation config
                    module_gen = data.get("generation", {})
                    self.generation_config.update(module_gen)
                    
                    execution = data.get("execution", {})
                    self.num_runs = execution.get("min_runs", 1)
        except Exception as e:
            logger.warning("Failed to load module config: %s", e)

    def load_questions(self, assets_dir: str = None):
        """Lädt die Liste an CSV-Tasks."""
        self.questions = self.loader.load_tasks()

    def execute(self, model: str, llm_client: Any, provider: str = "ollama", **kwargs) -> BenchmarkResult:
        """
        Führt das Batch-Modul aus.
        """
        if not self.questions:
            self.load_questions()

        total_score = 0.0
        details = []
        total_time = 0.0
        total_tokens = 0
        success_count = 0
        
        system_prompt = SYSTEM_PROMPT

        print("Fortschritt:")
        for idx, q in enumerate(self.questions, 1):
            q_name = str(q.get('name', q.get('id', 'Unknown')))[:25]
            print(f"   ⏳ [{idx}/{len(self.questions)}] {q_name}: Test läuft...", end="\r", flush=True)

            task_prompt = f"Task: {q['name']}\nDescription: {q['description']}\nTools: {q['tools']}\nGenerate the bash commands to solve this:"
            
            start_t = time.time()
            output_text = ""
            try:
                # Extract specific generation parameters from config
                temp = self.generation_config.get("temperature", 0.1)
                top_p = self.generation_config.get("top_p", 0.9)
                
                output_text = llm_client.query(
                    model=model,
                    provider=provider,
                    system=system_prompt,
                    prompt=task_prompt,
                    temperature=temp,
                    top_p=top_p
                )
            except Exception as e:
                output_text = f"Error calling model: {e}"
                import traceback
                traceback.print_exc()
                
            elapsed = time.time() - start_t
            
            # Approximation for missing metadata
            tokens = int(len(output_text) / 4)
                
            eval_res = self.evaluator.evaluate(q, output_text)
            
            # Compile stats
            total_time += elapsed
            total_tokens += tokens
            total_score += eval_res['solutionquality']
            if eval_res['status'] == 'success':
                success_count += 1
            
            details.append({
                "task_id": q["id"],
                "task_name": q["name"],
                "model_output": output_text,
                "eval": eval_res,
                "time_s": elapsed
            })
            
            # Standard Console Output for Module Iterator Mode
            pct = eval_res.get('solutionquality', 0.0)
            if pct >= 95:
                badge_inline = "🏆"
            elif pct >= 85:
                badge_inline = "⭐"
            elif pct >= 75:
                badge_inline = "🟢"
            elif pct >= 60:
                badge_inline = "🟡"
            elif pct >= 50:
                badge_inline = "🟠"
            else:
                badge_inline = "🔴"
                
            token_str = f"{tokens / 1000.0:.1f}k T" if tokens > 1000 else f"{tokens} T"
            status_icon = "✓" if eval_res.get('status') == 'success' else "✗"
            
            print(" " * 80, end="\r")
            print(f"   {status_icon} [{idx}/{len(self.questions)}] {q_name:<25}: {pct:>5.1f}% {badge_inline} | {token_str} | {elapsed:>4.1f}s")

        avg_score = total_score / len(self.questions) if self.questions else 0.0
        
        if avg_score >= CLI_GOLD_THRESHOLD:
            badge = "CLI Gold 🥇"
        elif avg_score >= CLI_SILVER_THRESHOLD:
            badge = "CLI Silver 🥈"
        elif avg_score >= CLI_BRONZE_THRESHOLD:
            badge = "CLI Bronze 🥉"
        else:
            badge = "CLI Fail ❌"
        
        report = {
            "status": "success",
            "score": avg_score,
            "badge": badge,
            "success_rate": f"{(success_count/max(len(self.questions),1))*100:.1f}%",
            "details": details
        }
        
        return BenchmarkResult(
            status="success",
            primary_score=float(avg_score),
            rendered_value=f"{badge} ({avg_score:.1f}/100)",
            execution_time=float(total_time),
            tokens_used=int(total_tokens),
            cost_usd=0.0,
            raw_response=json.dumps(report),
            model_version="unknown",
            data={
                "subscores": {
                    "routine": avg_score, 
                    "reasoning": avg_score * (success_count/max(len(self.questions),1))
                },
                "raw_score": avg_score / 100.0,
                "display": {"summary": f"{success_count}/{len(self.questions)} Tasks Successful"}
            }
        )
