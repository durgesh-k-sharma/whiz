# PRD: Whiz -- A Recursive Language Model Coding Agent

## Problem Statement

Existing coding agents (Claude Code, Codex CLI, etc.) struggle with large codebases. They either truncate context, lose track of distant dependencies, or degrade in quality as input size grows. Developers working with repositories that exceed their model's context window have no good tool for the job.

The Recursive Language Model (RLM) paradigm (Zhang, Kraska, Khattab 2025) solves this by equipping an LLM with a persistent Python REPL where the input is stored as a variable, not copied into the context window. The LLM can recursively call itself on chunks of the input, decomposing arbitrarily long contexts. This paper-demonstrated approach has not yet been productized into a developer tool.

Whiz is a CLI coding agent and library that implements the RLM paradigm. It gives developers a tool that can reason over codebases, documents, and tasks 100x larger than the underlying model's context window, with the full power of Python available for decomposition, parallel exploration, and programmatic file manipulation.

## Solution

Whiz is a developer CLI tool (`whiz`) and importable Python library (`from whiz import Session`) that implements the RLM inference paradigm. Users interact with it through:

- **Interactive Mode** (`whiz`): a persistent Session where the user issues a prompt, watches the agent work, and can steer mid-execution with follow-up messages.
- **One-shot Mode** (`whiz run "..."`): the agent processes a single prompt and exits with the result.
- **Library API** (`from whiz import Session`): other Python programs can create and drive RLM sessions programmatically.

The agent stores the codebase Index and user prompt as variables in a persistent Python REPL. Instead of choosing from a fixed set of tools, the LLM writes arbitrary Python code -- it can define variables, write loops, import standard library modules, call Search to grep across the codebase, ReadFiles/EditFile/RunTests for file manipulation, and SubLLM to recursively decompose sub-problems in parallel. The LLM controls its own workflow until it signals Complete.

## User Stories

### Setup and Configuration

1. As a developer, I want to install Whiz via `pip install whiz`, so that I can use it quickly without complex setup.
2. As a developer, I want to provide my API keys (OpenAI, Anthropic, OpenRouter) via environment variables, so that Whiz can call model backends without hardcoding secrets.
3. As a developer, I want to configure Whiz in `~/.whiz/config.yaml`, so that I don't have to specify backend and model on every invocation.
4. As a developer, I want project-level overrides in `.whiz/config.yaml`, so that different projects can use different models or recursion limits.
5. As a developer, I want CLI flags to override any config value, so I can quickly change behavior for a single session.
6. As a developer, I want named Profiles (e.g. `--profile fast`, `--profile powerful`), so I can quickly switch between preset configurations without editing config files.
7. As a developer, I want Whiz to work with local models via Ollama, so that I can use it without cloud API costs or for privacy-sensitive codebases.
8. As a developer, I want Whiz to support OpenRouter, so I can access many models through a single API key.

### Interactive Mode

9. As a developer, I want to type `whiz` and enter Interactive Mode, so that I can have a back-and-forth coding session with the agent.
10. As a developer, I want to see the agent's Trajectory in the terminal (actions taken, REPL output, sub-LLM calls), so that I can understand what it's doing and trust its reasoning.
11. As a developer, I want to steer mid-session by typing a follow-up message that gets injected into the REPL, so that I can redirect the agent without starting over.
12. As a developer, I want Ctrl+C to cancel the session cleanly, so that I can stop a runaway agent without losing the Trajectory log.
13. As a developer, I want `--verbose` and `--quiet` flags, so that I can control how much terminal output I see during a session.

### One-shot Mode

14. As a developer, I want `whiz run "refactor the auth module"` to run a single task and exit, so that I can use Whiz in scripts or CI.
15. As a developer, I want one-shot mode to return a clear exit code (0 for success, 1 for failure), so that CI pipelines can detect whether the agent completed its task.
16. As a developer, I want one-shot mode to support `--dry-run`, so that the agent writes changes to a temp directory and shows a diff without touching my working tree.

### Core Agent Behavior

17. As a developer, I want the agent to handle codebases larger than the model's context window by recursively decomposing the problem via SubLLM, so that I can work with any size repository.
18. As a developer, I want the agent to respect a configurable recursion depth limit (default 5, range 1-20), so that runaway recursion doesn't consume excessive tokens or API costs.
19. As a developer, I want the agent to run Sub-LLM calls in parallel when the LLM generates parallelizable code, so that large tasks complete faster.
20. As a developer, I want the agent to automatically compact REPL history when context approaches the model limit, so that long-running sessions don't silently fail.
21. As a developer, I want the agent to have access to the full Python standard library inside the REPL, so it can use subprocess, pathlib, json, regex, etc. without restrictions.
22. As a developer, I want convenience tools (search, read_files, edit_file, run_tests) pre-injected as Python callables, so the LLM can perform common coding tasks with minimal boilerplate.
23. As a developer, I want the REPL to persist state across turns, so the LLM can define variables early and reference them later in the same Session.

### File Operations

24. As a developer, I want the agent to modify files in the working directory by default, so the changes are immediately visible (like any other developer tool).
25. As a developer, I want `--dry-run` to write changes to a temp directory and show a unified diff, so I can review before applying.
26. As a developer, I want `--auto-commit` to run `git commit` with an LLM-generated commit message after the session, so the changes are versioned automatically.
27. As a developer, I want the agent to handle file conflicts gracefully (e.g., if a file is modified externally during the session), so that work isn't silently lost.

### Search and Codebase Index

28. As a developer, I want the agent to Search for code patterns (even in large codebases) without loading entire files into context, so that it can find relevant definitions and usages efficiently.
29. As a developer, I want the Search tool to support semantic/vector search (with a grep fallback), so that it can find conceptually related code even when the exact keywords don't match.
30. As a developer, I want the codebase Index to be generated at session start, so the agent has awareness of the project structure from the beginning.

### Environment and Sandboxing

31. As a developer, I want the default Environment to be the local REPL (in-process), so there's no setup friction or latency overhead.
32. As a developer, I want to opt into Docker sandboxing via config or flag, so I can run the agent against untrusted codebases safely.
33. As a developer, I want cloud sandbox support (Modal, E2B, Daytona) stubbed in the architecture, so that they can be implemented later without refactoring.

### Trajectory and Logging

34. As a developer, I want every Session's Trajectory written to `~/.whiz/logs/`, so I can review what happened after the fact.
35. As a developer, I want the Trajectory log to capture every LLM-generated code snippet, REPL output, and Sub-LLM call result, so I have full auditability.
36. As a developer, I want token usage and cost information in the Trajectory, so I can track API spend per session.

### Library API

37. As a product engineer, I want to import Whiz as a Python library (`from whiz import Session`), so that I can build custom tools on top of the RLM paradigm.
38. As a product engineer, I want the library API to support both sync (`session.run()`) and async (`await session.arun()`) execution, so it fits into both scripts and async applications.

### DX and Error Handling

39. As a developer, I want clear error messages when my API keys are missing or invalid, so I can fix config issues quickly.
40. As a developer, I want the agent to self-correct when its generated Python code fails (syntax errors, FileNotFoundError, etc.), so that minor mistakes don't derail the entire session.
41. As a developer, I want the agent to surface meaningful errors (not raw Python tracebacks) when something goes wrong at the REPL level.

## Implementation Decisions

### Architecture: Two-Level Loop

Whiz is structured as two nested loops. The Orchestrator (outer loop) manages the conversation lifecycle -- user I/O, Session creation, recursion depth/round limits, compaction triggers, and model configuration. The REPL (inner loop) runs the LLM thinking cycle -- generate Python code, execute it, feed output back, repeat until the LLM signals Complete or hits the round limit.

### REPL Environment (Local, Default)

The default REPL runs via Python `exec()` in the same process. State persists across turns in a dictionary namespace. Stdlib modules (subprocess, pathlib, os, json, re, etc.) are always available. Convenience tools (Search, ReadFiles, EditFile, RunTests, SubLLM, Complete) are injected into the REPL namespace as callables.

REPL errors are surfaced to the LLM as concise messages (error type + 1-2 lines), not full tracebacks. No automatic self-retry; the LLM reads the error from REPL history and self-corrects on the next turn.

### Model Backends

Whiz supports four model backends: OpenAI, Anthropic, OpenRouter, and Ollama. Each backend implements a common interface (`complete(messages, model) -> response`) and handles its own authentication (via environment variables) and API specifics.

Sub-LLM calls use the model specified in global config (`sub_model` key), defaulting to the same model as the parent when not set. Sub-call model preference is configurable only via global config/CLI, not per-call in the REPL.

### Configuration

Configuration is three-tiered: `~/.whiz/config.yaml` (global) < `.whiz/config.yaml` (project) < CLI flags. All tiers merge with later tiers winning.

Profiles are named presets (fast, balanced, powerful) defined in config. The active profile is selected by `active_profile` in config or `--profile` on CLI.

Example config shape:
```yaml
profiles:
  fast:
    backend: ollama
    model: llama3
    sub_model: ollama/llama3
    recursion:
      max_depth: 3
  balanced:
    backend: openai
    model: gpt-4o
    sub_model: ollama/llama3
    recursion:
      max_depth: 5
  powerful:
    backend: openrouter
    model: openrouter/auto
    sub_model: ollama/llama3
    recursion:
      max_depth: 10
active_profile: balanced
environment: local
logging:
  dir: ~/.whiz/logs
  level: info
```

### Recursion

Sub-LLM calls are dispatched via a `sub_llm` callable in the REPL. Sub-calls run in parallel when the LLM generates parallelizable code. Each sub-call gets its own child Session and REPL, with depth tracked globally. Hard depth limit from config (default 5, allowed range 1-20).

The Sub-LLM callable has a clean interface: `sub_llm(prompt: str, context: str) -> str`. The LLM can write loops, map over chunks, and control recursion shape programmatically.

### Compaction

When REPL history token count exceeds a model-specific threshold, an LLM summarization pass replaces the accumulated history with a compact summary. The summary preserves important intermediate results (found file contents, computed values, key observations) and discards verbose output (full file dumps, noisy logs). Compaction events are logged in the Trajectory.

### Interactive Mode

Interactive mode uses async I/O so the Orchestrator can listen for user input while the REPL is executing (or waiting on Sub-LLM calls). User steering messages are injected into the REPL as `_user_steer` variables between turns. Ctrl+C triggers a clean shutdown: cancels active Sub-LLM calls, writes partial Trajectory to disk, and exits with a clear message.

### Search

The Search tool is exposed as a `search(query: str)` callable in the REPL. The interface is backend-agnostic: it accepts a query string and returns matching file paths with relevant snippets. Day one implementation uses grep/ripgrep under the hood. The architecture supports swapping to semantic/vector search (embeddings + vector DB) without changing the agent code or REPL prompt.

### Index

At session start, Whiz generates a lightweight Index of the codebase -- a truncated file tree and, if present, the first ~200 lines of the README. These are injected into the REPL as `file_tree` and `readme` variables. The agent explores deeper via Search and ReadFiles on demand.

### Trajectory Logging

Every Session writes a Trajectory file to `~/.whiz/logs/` containing: timestamped entries for each LLM-generated code snippet, REPL output, Sub-LLM call (with depth and results), compaction events, steering inputs, errors, and final result. Terminal output uses Rich for formatted display at configurable verbosity levels.

### Python and Packaging

Whiz is Python 3.11+, uses a `src/` layout (`src/whiz/`), and is distributed via PyPI. Dependencies: `click` (CLI), `pyyaml` (config), `rich` (terminal output), `httpx` (model API calls), `openai` + `anthropic` (backend SDKs). Cloud sandbox stubs have soft dependencies -- imports are guarded and raise a clear error message if a cloud package is not installed.

### Sandboxing (Future)

Docker Environment is implemented as a concrete environment backend. Cloud sandboxes (Modal, E2B, Daytona, Prime) have stub classes that implement the same Environment interface but raise `NotImplementedError` with a clear message. This ensures the architecture is ready and no build issues arise from their presence.

## Testing Decisions

### Test Framework

PyTest is the test framework. Tests are organized into `tests/unit/`, `tests/integration/`, and `tests/mocks/`.

### Mock LLM

A `MockLLM` class (in `tests/mocks/llm.py`) takes a list of scripted responses and returns them in order. This exercises the full Orchestrator and REPL flow without calling a real model. MockLLM also records all calls made to it, enabling assertions about what prompts were sent.

### Unit Tests

Unit tests cover: Config loading and merging (profiles, env var expansion, CLI overrides), REPL execution (code evaluation, state persistence, error formatting), Tool functions (Search, EditFile, RunTests -- filesystem operations with temporary directories), Recursion dispatch (depth limiting, parallel sub-call aggregation, parent-child result propagation).

Unit tests never call a real model API. All model interactions go through MockLLM.

### Integration Tests

Integration tests exercise the full Session flow (Orchestrator + REPL + Sub-LLM) against a MockLLM with scripted multi-turn conversations. These verify: the two-level loop works end-to-end, steering inputs are delivered mid-session, compaction triggers correctly, depth limits are enforced.

Integration tests that require a real model are placed in a separate suite (marked `@pytest.mark.e2e`) and skipped unless API key environment variables are present.

### Test Quality

Tests verify external behavior (Session output, Trajectory contents, file modifications), not implementation details (private methods, internal state representation). REPL internals are tested through their observable effects (variables available to the next turn, error messages surfaced to the LLM).

## Out of Scope

- **GUI/desktop application.** Whiz is CLI and library only for this PRD.
- **Multi-repository Sessions.** A single Session operates on one project root.
- **Collaborative/multi-user Sessions.** One user per Session.
- **Full semantic search in v1.** Grep-backed search ships first; vector search is a future enhancement within the existing Search interface.
- **Cloud sandbox implementations (Modal, E2B, Daytona, Prime).** Stubs only. Implementing cloud sandboxes is not in scope.
- **Training/fine-tuning RLM models.** Whiz uses existing models. The training pipeline from the RLM paper is a separate concern.
- **Non-English language support in prompts.** The agent operates in English.

## Further Notes

### Performance Considerations

- Parallel Sub-LLM calls are the primary performance lever for large tasks. The Orchestrator should use `asyncio.gather` or `concurrent.futures` to dispatch sub-calls concurrently.
- Compaction introduces additional LLM calls. The token threshold should be set conservatively (e.g., 70% of model context limit) to avoid frequent compactions.
- The Index generation at session start should be fast and stateless -- walk the file tree, read no file contents.

### Open Questions

- Whether the REPL prompt (the system message provided to the LLM at the start of the inner loop) should be user-configurable or fixed. Starting with a fixed, well-designed prompt; making it configurable is a future enhancement.
- Whether to support checkpointing (saving and resuming a Session mid-execution). Not in scope for v1 but the Trajectory log provides enough information to reconstruct checkpointing later.

### Relation to RLM Paper

This product implements the RLM inference paradigm from "Recursive Language Models" (Zhang, Kraska, Khattab, arXiv:2512.24601). The core contribution of that work -- giving the LLM a persistent Python REPL with recursive self-calling -- is the foundation of Whiz. The product-specific additions are: the CLI, configuration system, multi-backend model support, interactive steering, trajectory logging, and the coding-agent tool set (Search, EditFile, etc.).
