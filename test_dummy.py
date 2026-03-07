from utils.llm_client import LLMClient

try:
    c = LLMClient()
    print("Inited")
    res = c.generate('dolphin-llama3:8b', prompt='hi')
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()
