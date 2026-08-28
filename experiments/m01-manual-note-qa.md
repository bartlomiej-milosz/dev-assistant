# M01 — Answering questions from a manually supplied note

**Model** `qwen3.5:9b` in Ollama

**Setup** Both prompts were sent in the same conversation.

## Trial 1 — The note contains the answer

**Prompt**

```text
Answer using only the note. If information is missing, say so explicitly. Note: On Linux, I check which process is listening on port 8000 with `sudo ss -ltnp 'sport = :8000'`. Question: Which command do I use to check what is listening on port 8000?
```

**Expected result** The model gives the command `sudo ss -ltnp 'sport = :8000'`.

**Model response**

> The command is `sudo ss -ltnp 'sport = :8000'`.

**Thinking time reported by the interface** 8.6 s

## Trial 2 — The note lacks the answer

**Prompt**

```text
Using the same note, tell me the PID of the process on port 8000.
```

**Expected result** The model says that the note does not provide the PID.

**Model response**

> The note does not contain the PID of the process on port 8000.

**Thinking time reported by the interface** 9.9 s

## Conclusion

The model reproduced the command from the note and correctly identified that the PID was missing. The note was included in the first prompt and remained available in the conversation context for the follow-up question.
