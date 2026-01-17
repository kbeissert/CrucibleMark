
import sys
from pathlib import Path
import time
import yaml

# Add root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from utils.llm_client import LLMClient

def test_trap():
    client = LLMClient()
    model = "qwen2.5:14b-instruct"
    
    asset_path = "benchmark_modules/reasoning_logic/assets/asset_5c_adversarial_robustness.yaml"
    with open(asset_path) as f:
        data = yaml.safe_load(f)
        prompt = data["prompt"]
        
    print(f"--- Running Trap Test on {model} ---")
    response = client.query(model, prompt, provider="ollama", temperature=0.6)
    
    print("\n--- RESPONSE ---")
    print(response)
    print("\n--- END RESPONSE ---")
    
    # Check trap keywords
    trap_keywords = ["impossible", "unmöglich", "mutually exclusive", "contradiction", "widerspruch", "schließen sich aus", "nicht machbar", "nicht realisierbar", "technisch ausgeschlossen"]
    resp_lower = response.lower()
    
    detected = [k for k in trap_keywords if k in resp_lower]
    print(f"\nTrap Keywords Found: {detected}")

if __name__ == "__main__":
    test_trap()
