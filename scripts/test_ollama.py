import requests, os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OLLAMA_API_KEY")

r = requests.post(
    "https://ollama.com/api/chat",
    headers={"Authorization": f"Bearer {key}"},
    json={
        "model": "gpt-oss:120b",
        "messages": [{"role": "user", "content": "test"}],
        "stream": False,
    },
)
print(r.status_code)
print(r.text)