# Changelog

## [0.1.0] - 2026-06-01

### Initial Release

- Recursive Language Model (RLM) inference paradigm
- Persistent Python REPL with stdlib + tool injection
- Orchestrator outer loop with session management, depth/round limits, trajectory logging
- Sub-LLM recursion with parallel execution and configurable depth limit
- LLM-based context compaction when history exceeds token threshold
- Interactive mode with mid-session steering via `_user_steer` injection
- CLI: `whiz run` (one-shot) and `whiz interactive` (interactive)
- Model backends: OpenAI, Anthropic Claude, OpenRouter, Ollama
- Execution environments: local (default), Docker, cloud sandbox stubs (Modal, E2B, Daytona, Prime)
- Codebase indexing: file tree generation, README extraction, `.gitignore`-aware filtering
- Search tool: grep-backed with semantic-ready interface
- Filesystem tools: read_files, edit_file, run_tests (with path traversal protection)
- Dry run mode and auto-commit
- Library API: `Session.run()` / `Session.arun()`
- Configuration: profiles, global + project YAML, CLI overrides
- Rich terminal output and JSONL trajectory logging to `~/.whiz/logs/`
- 147 unit tests
