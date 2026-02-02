#!/usr/bin/env python3
"""
Scaffolding Script for new CrucibleMark Benchmark Modules.
Creates directory structure and boilerplate files following the MVC architecture.
Usage: python scripts/scaffold_module.py [module_name]
"""

import sys
from pathlib import Path
from datetime import datetime

# Templates
TEMPLATE_CONFIG = """# {display_name} Configuration
# ========================================

metadata:
  id: "{module_name}"
  name: "{display_name}"
  version: "0.1.0-alpha"
  description: "TODO: Add description for {display_name}"
  author: "CrucibleMark User"
  created: "{date}"
  tags:
    - todo

integration:
  leaderboard:
    enable_scoring: true
    default_contribution:
      routine: 0.5
      reasoning: 0.5
    columns:
      - id: "total_score"
        label: "{display_name}"
        weight: 1.0

execution:
  test_class: "{class_name}Test"
  assets_dir: "assets"

# Internal Module Configuration
config:
  categories:
    default:
      weight: 1.0
"""

TEMPLATE_TEST = """\"\"\"
Controller for {display_name} Module.
Orchestrates the benchmark execution using the standard MVC pattern.
\"\"\"

import time
from typing import Dict, Any, List
from benchmark_modules.base_test import BaseTest
from .core.evaluators import {class_name}Evaluator

class {class_name}Test(BaseTest):
    \"\"\"
    Controller class for {display_name}.
    Handles LLM communication and delegates scoring to the core evaluator.
    \"\"\"
    
    def __init__(self):
        super().__init__()
        # Initialize the separated logic layer
        self.evaluator = {class_name}Evaluator()
    
    def execute(self, model: str, llm_client, provider: str = 'ollama') -> Dict[str, Any]:
        \"\"\"
        Executes the test for a single model and asset.
        \"\"\"
        # 1. Load Asset Data
        if not self.asset:
            return {"error": "No asset loaded"}
            
        system_prompt = self.asset.get('input', {}).get('system_prompt', "You are a helpful assistant.")
        user_prompt = self.asset.get('input', {}).get('prompt', "")
        
        # 2. Execute LLM Call
        start_time = time.time()
        try:
            # Note: Adjust call signature if needed (some modules use specific prompt formats)
            response = llm_client.generate(
                model=model, 
                prompt=user_prompt,
                system=system_prompt
            )
        except Exception as e:
            return {
                "status": "error",
                "reason": str(e),
                "duration": 0
            }
        duration = time.time() - start_time
        
        # 3. Return Raw Data (Scoring happens in next step)
        return {
            "status": "success",
            "model": model,
            "raw_response": response,
            "execution_time": duration
        }

    def score_response(self, response: Dict[str, Any]) -> float:
        \"\"\"
        Calculates the score based on the raw response.
        Logic is delegated to self.evaluator in core/.
        \"\"\"
        if response.get("status") != "success":
            return 0.0
            
        result = self.evaluator.evaluate(
            response_text=response.get("raw_response", ""),
            asset=self.asset
        )
        
        # Store detailed breakdown for the CSV output or UI
        self.latest_score_details = result.get('details', {})
        
        return result.get('score', 0.0)
"""

TEMPLATE_EVALUATOR = '''"""
Pure Logic Layer for {display_name}.
Contains all scoring algorithms. Zero dependencies on LLM clients or IO.
"""

from typing import Dict, Any

class {class_name}Evaluator:
    """
    Evaluates model outputs against asset criteria.
    """
    
    def evaluate(self, response_text: str, asset: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main evaluation entry point.
        
        Args:
            response_text: The raw string output from the LLM.
            asset: The loaded definition of the test case.
            
        Returns:
            Dict with keys 'score' (float 0-100) and 'details' (Dict).
        """
        
        # 1. Preprocessing (e.g. remove think tags)
        clean_text = self._clean_response(response_text)
        
        # 2. Logic Implementation (TODO: Add your custom logic here)
        # Example: Keyword matching
        expected_keywords = asset.get('evaluation', {}).get('keywords', [])
        
        score = self._calculate_dummy_score(clean_text, expected_keywords)
        
        return {
            "score": score,
            "details": {
                "length": len(clean_text),
                "keyword_match_rate": score
            }
        }
    
    def _clean_response(self, text: str) -> str:
        if not text:
            return ""
        return text.strip()
        
    def _calculate_dummy_score(self, text: str, keywords: list) -> float:
        # Placeholder logic
        if not text:
            return 0.0
        return 50.0 # TODO: Implement real scoring
'''

TEMPLATE_INIT = "\"\"\"\nExpose the Test Class for dynamic loading.\n\"\"\"\nfrom .test import {class_name}Test\n"

TEMPLATE_README = """# {display_name} Module

**Status:** Alpha
**Type:** {score_group}

## Overview
TODO: Describe what this benchmark module tests.

## Methodology
How is the score calculated?
1. Criteria A
2. Criteria B

## Assets
Describe the assets in `assets/`.
"""

TEMPLATE_ASSET = """meta:
  id: "{module_name}_001"
  difficulty: 1
  name: "Example Test Case"

input:
  system_prompt: "You are an expert."
  prompt: "Explain why rust is memory safe."

evaluation:
  keywords:
    - borrow checker
    - ownership
  min_length: 50
"""

def to_camel_case(snake_str):
    components = snake_str.split('_')
    return ''.join(x.title() for x in components)

def get_input(prompt, default=None):
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()

def main():
    print("🏗️  CrucibleMark Module Scaffolder")
    print("==================================\n")
    
    # 1. Gather Info
    if len(sys.argv) > 1:
        module_name = sys.argv[1]
        print(f"Module Key: {module_name}")
    else:
        module_name = get_input("Module Key (folder name, snake_case)", "new_module")
    
    display_name = get_input("Display Name", to_camel_case(module_name))
    class_name = to_camel_case(module_name)
    
    print("\nSelect Score Group:")
    print("1. routine   (Daily tasks, Writing, Documentation)")
    print("2. reasoning (Logic, Math, Coding)")
    print("3. info      (Informational only, e.g. Political Compass)")
    group_choice = get_input("Choice", "1")
    
    score_groups = {"1": "routine", "2": "reasoning", "3": "info"}
    score_group = score_groups.get(group_choice, "routine")
    
    # 2. Define Paths
    base_dir = Path("benchmark_modules") / module_name
    
    if base_dir.exists():
        print(f"\n❌ Error: Directory {base_dir} already exists!")
        sys.exit(1)
        
    # 3. Create Structure
    print(f"\n📂 Creating structure at {base_dir}...")
    (base_dir / "assets").mkdir(parents=True)
    (base_dir / "core").mkdir(parents=True)
    
    context = {
        "display_name": display_name,
        "module_name": module_name,
        "class_name": class_name,
        "score_group": score_group,
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    
    # 4. Write Files
    files = {
        "config.yaml": TEMPLATE_CONFIG.format(**context),
        "test.py": TEMPLATE_TEST.format(**context),
        "__init__.py": TEMPLATE_INIT.format(**context),
        "README.md": TEMPLATE_README.format(**context),
        "core/__init__.py": "",
        "core/evaluators.py": TEMPLATE_EVALUATOR.format(**context),
        f"assets/{module_name}_001.yaml": TEMPLATE_ASSET.format(**context)
    }
    
    for filename, content in files.items():
        path = base_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ Created {filename}")
        
    print("\n🎉 Module created successfully!")
    print("\nNext Steps:")
    print("1. Add the module to benchmark_config.yaml:")
    print("   modules:")
    print(f"     {module_name}:")
    print("       enabled: true")
    print(f"       path: \"benchmark_modules/{module_name}\"")
    print(f"2. Customize logic in {base_dir}/core/evaluators.py")
    print(f"3. Add assets to {base_dir}/assets/")

if __name__ == "__main__":
    main()
