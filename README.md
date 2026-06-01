# Whiz

**A CLI coding agent and library implementing the Recursive Language Model (RLM) paradigm.**

Whiz enables LLMs to handle arbitrarily long contexts — codebases, documents, multi-file reasoning — by equipping them with a persistent Python REPL they can programmatically explore and recursively decompose problems in.

Based on the research paper [Recursive Language Models](https://arxiv.org/abs/2512.24601) by Zhang, Kraska, and Khattab (MIT CSAIL, 2025).

## Features

- **Recursive Language Model (RLM) paradigm** — The LLM writes Python code in a persistent REPL, storing intermediate results as variables and calling itself recursively on sub-problems
- **Arbitrary context length** — Process inputs 100x+ beyond the model's native context window through recursive decomposition
- **Parallel sub-LLM calls** — Launch concurrent child sessions for batch processing
- **LLM-based context compaction** — Automatically summarizes REPL history when context approaches the model limit
- **Interactive mode** — Mid-session steering: redirect the agent while it's working
- **Multiple model backends** — OpenAI, Anthropic Claude, OpenRouter, Ollama (local)
- **Multiple execution environments** — Local (default), Docker, with cloud sandbox stubs (Modal, E2B, Daytona, Prime)
- **Dry run mode** — Preview changes without modifying files
- **Auto-commit** — Automatic git commits with LLM-generated messages
- **Rich trajectory logging** — Full audit trail of every REPL interaction, written to `~/.whiz/logs/`
- **Library API** — Use as a Python library (`from whiz import Session`) or CLI tool

## Installation

```bash
pip install whiz
```

Or install from source using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
git clone https://github.com/durgesh-k-sharma/whiz.git
cd whiz
make venv
source .venv/bin/activate
```

Or with vanilla Python:

```bash
git clone https://github.com/durgesh-k-sharma/whiz.git
cd whiz
python3 -m venv .venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[test]"
```

## Quick Start

### One-shot mode

Run a single task and exit:

```bash
export OPENROUTER_API_KEY="sk-or-..."
whiz run "refactor the authentication module"
```

Switch profiles with `--profile`:

```bash
whiz run --profile or-free "quick task"     # OpenRouter free tier
whiz run --profile or-claude "complex task" # Claude via OpenRouter
whiz run run "summarize"                   # GPT-4o via OpenRouter
```

### Interactive mode

Start an interactive session where you can steer mid-execution:

```bash
whiz interactive "explore the codebase and find all TODOs"
```

### Library API

Use Whiz programmatically from Python:

```python
from whiz import Session
from whiz.models import OpenAIModel

session = Session(
    model=OpenAIModel(model="gpt-4o"),
    project_root="/path/to/your/project",
    verbose=True,
)
result = session.run("refactor the auth module")
print(f"Result: {result.value}")
print(f"Rounds: {result.rounds}")

# Async with steering support:
result = await session.arun("explore the codebase")
```

## Configuration

Create a config file at `~/.whiz/config.yaml`:

```yaml
profiles:
  or-free:
    backend: openrouter
    model: openrouter/free
    sub_model: openrouter/free
    recursion:
      max_depth: 3
      max_repl_rounds: 50
    environment: local
  or-claude:
    backend: openrouter
    model: openrouter/anthropic/claude-sonnet-4
    sub_model: openrouter/anthropic/claude-sonnet-4
    recursion:
      max_depth: 5
      max_repl_rounds: 100
  or-gpt4o:
    backend: openrouter
    model: openrouter/openai/gpt-4o
    recursion:
      max_depth: 5
      max_repl_rounds: 100
  or-auto:
    backend: openrouter
    model: openrouter/auto
    recursion:
      max_depth: 5
      max_repl_rounds: 100
  ollama:
    backend: ollama
    model: llama3
    recursion:
      max_depth: 3
      max_repl_rounds: 50

# Default profile (pass --profile to override)
active_profile: or-free

logging:
  dir: ~/.whiz/logs
  level: info
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `OLLAMA_BASE_URL` | Ollama base URL (default: `http://localhost:11434`) |

## CLI Reference

```
whiz run <prompt>           Run a one-shot task
whiz interactive <prompt>   Start an interactive session
whiz --help                 Show help
```

Options:

| Flag | Description |
|------|-------------|
| `--profile` | Configuration profile to use |
| `--verbose` | Show REPL execution trace |
| `--quiet` | Suppress output |
| `--dry-run` | Preview changes without applying |
| `--max-rounds` | Max REPL rounds (overrides profile) |
| `--auto-commit` | Auto git-commit after session |

## Architecture

```
User Prompt
    │
    ▼
┌──────────────────────────────────────────────┐
│  Orchestrator (Outer Loop)                   │
│  - Session management                        │
│  - Depth/round limits                        │
│  - Compaction triggers                       │
│  - Trajectory logging                        │
│  ┌────────────────────────────────────────┐  │
│  │  REPL (Inner Loop)                     │  │
│  │  - Persistent Python namespace         │  │
│  │  - Stdlib + injected tools             │  │
│  │  - Variable persistence across turns   │  │
│  │  - History tracking                    │  │
│  │                                        │  │
│  │  Tools:                                │  │
│  │  - search(query) → grep results        │  │
│  │  - read_files(paths) → file contents   │  │
│  │  - edit_file(path, content) → write    │  │
│  │  - run_tests() → pytest output         │  │
│  │  - sub_llm(prompt, ctx) → child result │  │
│  │  - complete(value) → signal done       │  │
│  │                                        │  │
│  │  Context injected:                     │  │
│  │  - file_tree, readme, project_root     │  │
│  │  - user_prompt                         │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
    │
    ▼
SessionResult(value, rounds, trajectory)
```

## How It Works

1. **Session start**: The Orchestrator indexes the codebase (file tree + README) and injects it as variables into a fresh Python REPL
2. **Inner loop**: The LLM generates Python code → the REPL executes it → output feeds back → repeat
3. **Recursion**: The LLM can call `sub_llm()` to spawn child sessions for sub-problems, with parallel execution and depth tracking
4. **Compaction**: When REPL history grows too large, an LLM summarizes it, preserving important variables
5. **Completion**: The LLM calls `complete(value)` to signal done and return the result

## Development

```bash
# Setup (recommended)
make venv
source .venv/bin/activate

# Run tests
make test
# or
uv run pytest tests/unit/

# Run with coverage
make test-cov

# Quick smoke test
whiz run --profile or-free "say hello"
```

## Roadmap

- [ ] Full semantic search (embeddings + vector DB)
- [ ] Cloud sandbox implementations (Modal, E2B, Daytona, Prime)
- [ ] Session checkpointing (save/resume)
- [ ] Multi-repository sessions
- [ ] Non-English language support

## Research

This project implements the RLM inference paradigm from:

> **Recursive Language Models**
> Alex L. Zhang, Tim Kraska, Omar Khattab
> MIT CSAIL, 2025
> [arXiv:2512.24601](https://arxiv.org/abs/2512.24601)

## License

MIT
