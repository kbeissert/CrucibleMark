from utils.providers.openai import OpenAIClient

client = OpenAIClient({"defaults": {}})
# mock client
class MockChat:
    def create(self, **kwargs):
        import json
        print(json.dumps(kwargs, ensure_ascii=False))
        class M:
            model = "mock"
            id = "mock"
            usage = None
            choices = []
        return M()

client._client = type("Mock", (), {"chat": type("MockChat", (), {"completions": MockChat()})()})()
client.query(
    model="gpt-4o",
    prompt="hello\nworld",
    temperature=0.7,
    max_tokens=100
)
