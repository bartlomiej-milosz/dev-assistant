from pathlib import Path

import httpx2
from httpx2 import Response


def main() -> None:
    """Entry point for the dev-assistant command-line interface."""
    prompt: str = Path("experiments/resources/m03-port-8000-prompt.md").read_text()
    response: Response = httpx2.post(
        url="http://localhost:11434/api/chat",
        json={
            "model": "qwen3.5:9b",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=120.0,
    )
    response.raise_for_status()
    print(response.json()["message"]["content"])
