import ollama
import sys

print("Reproducing issue with gpt-oss:20b-low...")

model = "gpt-oss:20b-low"
prompt = "In a field there are 10 sheep. All but 9 die. How many remain?"

system_prompt = (
    "You are a logic expert. Solve the given problem step-by-step. "
    "Show your reasoning process clearly ('Chain of Thought'). "
    "Finally, provide the clear Answer."
)

try:
    # Mimic the setup in provider_clients.py
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    options = {"temperature": 0.1, "num_predict": 32768}
    
    print("Attempting chat (stream=True)...")
    stream = ollama.chat(model=model, messages=messages, stream=True, options=options)
    
    for chunk in stream:
        print(chunk['message']['content'], end="", flush=True)
        
    print("\nSuccess!")

except Exception as e:
    print(f"\nCaught exception: {e}")
    if hasattr(e, 'response'):
         print(f"Response: {e.response}")
