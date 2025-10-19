
# Structured Outputs Update (Drop-in)

This update replaces `src/adventure/llm.py` to use **OpenAI Responses API + Structured Outputs**.
- Default model: `gpt-4o-mini` (override with `ADVENTURE_MODEL`).
- Enforces a strict JSON Schema with `response_format={"type":"json_schema", "json_schema": {..., "strict": true}}`.
- Requires `openai` Python SDK (1.40+ recommended).

**Install/upgrade SDK**

```bash
pip install --upgrade openai
```

**Environment**

```bash
export OPENAI_API_KEY=sk-...
# optional
export ADVENTURE_MODEL=gpt-4o-mini
```

Drop this `llm.py` into your existing project at `src/adventure/llm.py`.
