# ADR-0001: Two-Level Loop Architecture (Orchestrator + REPL)

We separate the agent into an outer Orchestrator loop and an inner REPL loop. The Orchestrator manages conversation lifecycle, user I/O, depth/round limits, and model configuration. The REPL loop is where the LLM actually "thinks" by generating and executing Python code in a persistent session.

This differs from traditional coding agents that operate turn-by-turn with discrete tool calls (read_file, write_file, bash). The RLM paradigm keeps the LLM inside a single long-running REPL where it can write loops, launch parallel sub-LLM calls, and accumulate state programmatically.

Alternative considered: a flat agent loop where each LLM turn produces a single tool call. This is simpler but cannot express the recursive decomposition that makes RLMs effective for long-context tasks.
