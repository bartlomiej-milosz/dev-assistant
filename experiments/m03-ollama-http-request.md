# M03 — Sending a request to Ollama from Python

**Model** `qwen3.5:9b` in Ollama

## Setup

Run `make run` from the project root. The CLI reads the [Markdown prompt](resources/m03-port-8000-prompt.md), which contains a short Linux note and a question about port 8000.

The CLI uses `httpx2` to send one `POST` request to `http://localhost:11434/api/chat`. The request puts the full prompt in `messages[0].content` and sets `stream` to `false` so Ollama returns a single JSON response. The CLI prints the text from `message.content`.

## Expected result

The CLI prints the command given in the note for checking what is listening on port 8000.

## Observed result

```bash
sudo ss -ltnp 'sport = :8000'
```

During verification, one request hit the 60-second read timeout. After increasing the timeout to 120 seconds, a retry returned the same command in Markdown backticks.

## Conclusion

The printed response matched the command in the note. The run verified the path from a Markdown file through the local Ollama API to the terminal.
