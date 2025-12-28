
import sys
from pathlib import Path
import time

# Add root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from utils.llm_client import LLMClient

def test_ollama_query():
    client = LLMClient()
    model = "qwen3:8b"
    
    # Load prompt from asset 002
    with open("benchmark_modules/ux_writing/assets/asset_002_button_labels.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)
        prompt = data["prompt"]
        context = data.get("context", "")
        full_prompt = f"{context}\n\n{prompt}"
    
    print(f"Querying {model} with prompt length {len(full_prompt)}...")
    start = time.time()
    try:
        response = client.query(model, full_prompt, provider="ollama")
        elapsed = time.time() - start
        print(f"Response received in {elapsed:.2f}s")
        print(f"Response length: {len(response)}")
        print(f"Response preview: {response[:100]}")
        
        if not response:
            print("WARNING: Empty response received!")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_ollama_query()
