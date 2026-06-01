# ADR-0002: REPL as the Primary Interaction Model

The LLM interacts with its environment by generating Python code that executes in a persistent REPL, not by selecting from a fixed set of tool calls. Standard library modules (subprocess, pathlib, os, json, re) are always available. Convenience tools (search, read_files, edit_file, run_tests, sub_llm, complete) are pre-injected as Python callables.

This gives the LLM full programming capabilities, not just the tools we anticipated. If a task requires something the convenience tools don't cover, the LLM can always fall back to raw Python -- shell out to git, parse with regex, use whatever library is installed.

Alternative considered: a fixed tool schema (like OpenAI's function calling or Claude's tool use). This is more constrained and can be useful for safety, but it fundamentally limits the LLM's ability to write programs that process its input -- which is the entire point of the RLM paradigm.
