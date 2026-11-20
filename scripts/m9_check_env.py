import urllib.request
import json
import os
import sys

print("Python version:", sys.version)

# Check Ollama
try:
    req = urllib.request.Request("http://localhost:11434/api/tags")
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode())
        print("Available Ollama models:")
        for m in data.get("models", []):
            print(f"  - {m.get('name')}: {m.get('size')} bytes")
except Exception as e:
    print("Ollama check failed:", e)

# Check config
try:
    from app.core.config import settings
    print("Settings:")
    print("  embedding_model:", settings.embedding_model)
    print("  ollama_model:", settings.ollama_model)
    print("  ollama_base_url:", settings.ollama_base_url)
    print("  generation_temperature:", settings.generation_temperature)
except Exception as e:
    print("Config check failed:", e)
