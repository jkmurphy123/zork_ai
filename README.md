
# Adventure Agent (Starter)

Generate a small old-school text adventure with 20–30 rooms and walk it in a CLI.
Topology is **procedural**, room **descriptions** come from an LLM (OpenAI).
Strict schema + validation keeps the map playable.

## Quick start

```bash
# 1) Python 3.11+ recommended
python -V

# 2) Create venv
python -m venv .venv
source ./.venv/bin/activate  # Windows: .\.venv\Scripts\activate

# 3) Install
pip install -e .

# 4) Set your OpenAI API key (bash shown)
export OPENAI_API_KEY=sk-...

# 5) Generate an adventure JSON (20–30 rooms)
python -m adventure.cli generate --title "The Brass Catacombs" --rooms 24 --theme ruins

# 6) Play it
python -m adventure.cli play out/adventure.json
```

## What’s inside

- **Procedural graph** with deterministic seed.
- **LLM decoration**: names & descriptions per room via OpenAI Chat Completions function-calling.
- **Pydantic schema** to guarantee structure.
- **Validator** to enforce connectivity, reciprocal exits, and direction normalization.
- **Tiny CLI engine** to walk around (`n,s,e,w,ne,nw,se,sw,up,down,in,out,enter,exit`, plus `look`, `where`, `exits`, `help`).

> If you prefer to run without an API key, pass `--dry` to `generate` to use template descriptions.

## Design

1. Build topology → 2. Validate/fix → 3. Ask LLM to write creative text for each node **without** changing exits.
This hybrid keeps maps sane and lets the model focus on prose.

## Notes

- Uses environment variable **OPENAI_API_KEY**.
- Uses **Chat Completions function-calling** to force JSON output that matches our schema.
- You can swap in the Responses API / Structured Outputs later with minimal changes.
