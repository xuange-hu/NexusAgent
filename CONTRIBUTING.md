# Contributing

Thanks for wanting to improve NexusAgent. It is a small, dependency-light agent framework; the
bar for a change is "a test that would have failed before it, and a one-line reason why".

## Setup

```bash
git clone https://github.com/xuange-hu/NexusAgent && cd NexusAgent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q
```

## Where things live

- `tools.py` — tool registry and the built-in tools.
- `llm_adapters.py` — LLM client adapters (stdlib OpenAI-compatible).
- `agent.py` — the run loop.
- `tests/` — pytest suite. Currently 50+ tests, all offline.

## Rules

- **No real network in tests.** Mock HTTP with `unittest.mock`. A test that hits the internet
  will fail in CI and will be rejected.
- **Every new tool or adapter path gets a test.** Pure helpers are preferred so they can be
  tested without an LLM or a network.
- Keep `requirements.txt` minimal. New third-party deps need a justification in the PR.

## Pull requests

Keep them small. Say, in the first line, what behaviour changed, and include the test that
exercises it.
