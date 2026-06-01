# Contributing to Whiz

## Development Setup

```bash
git clone https://github.com/durgesh-k-sharma/whiz.git
cd whiz
python -m venv .venv --python 3.12
source .venv/bin/activate
pip install -e ".[test]"
```

## Running Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest tests/unit/ --cov=whiz --cov-report=term-missing

# Run a specific test file
pytest tests/unit/test_repl.py -v

# Run E2E tests (requires API keys)
OPENAI_API_KEY=sk-... pytest tests/ -m e2e
```

## Project Structure

```
whiz/
├── src/whiz/              # Main package
│   ├── agent/             # Orchestrator, interactive, recursion, compaction
│   │   ├── loop.py        # Orchestrator (outer agent loop)
│   │   ├── interactive.py # InteractiveSession (async I/O + steering)
│   │   ├── recursion.py   # Sub-LLM callable factory
│   │   └── compaction.py  # LLM-based context compaction
│   ├── cli.py             # Click CLI entry points
│   ├── config.py          # Config loading, profiles
│   ├── context/           # Codebase indexing
│   │   └── indexer.py     # File tree + README extraction
│   ├── logging/           # Trajectory logging
│   │   └── trajectory.py  # JSONL session logs
│   ├── models/            # Model backends
│   │   ├── base.py        # BaseModel, LLMResponse
│   │   ├── openai.py      # OpenAI backend
│   │   ├── anthropic.py   # Anthropic backend
│   │   ├── openrouter.py  # OpenRouter backend
│   │   └── ollama.py      # Ollama backend
│   ├── repl/              # REPL environments
│   │   ├── base.py        # BaseEnvironment abstract class
│   │   ├── core.py        # LocalREPL (in-process Python exec)
│   │   ├── docker.py      # DockerEnvironment
│   │   └── cloud/         # Cloud sandbox stubs
│   ├── tools/             # REPL tool functions
│   │   ├── search.py      # grep-backed search
│   │   └── filesystem.py  # read_files, edit_file, run_tests
│   └── api.py             # Public library API (Session class)
├── tests/
│   ├── unit/              # Unit tests (no API calls)
│   ├── integration/       # Integration tests
│   └── mocks/             # MockLLM for testing
├── docs/
│   ├── adr/               # Architecture Decision Records
│   └── agents/            # Agent skill configuration
└── examples/              # Usage examples
```

## Code Style

- Python 3.11+
- Type hints on all public functions
- Docstrings on all public classes and functions
- Test-driven: write failing tests before production code
- All tests must pass before merging

## Architecture Decisions

See `docs/adr/` for architectural decision records. Key decisions:

- **Two-level loop** (Orchestrator + REPL) -- ADR-0001
- **REPL as primary interaction model** (not fixed tool calls) -- ADR-0002
- **Local REPL as default sandbox** -- ADR-0003
- **LLM-based compaction** -- ADR-0004
- **Interactive mode with steering** -- ADR-0005
- **In-place file mutation, dry-run via flag** -- ADR-0006

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests first, then implementation
4. Ensure all tests pass (`pytest tests/unit/`)
5. Update documentation as needed
6. Submit a pull request

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag: `git tag v0.x.x`
4. Push: `git push --tags`
5. Build: `hatch build`
6. Publish: `hatch publish`
