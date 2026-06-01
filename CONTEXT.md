# Whiz

Whiz is a CLI coding agent and library that implements the Recursive Language Model (RLM) paradigm. It enables LLMs to handle arbitrarily long contexts -- codebases, documents, multi-file reasoning -- by equipping them with a Python REPL they can programmatically explore and recursively decompose problems in.

## Language

**RLM (Recursive Language Model):**
An inference paradigm where an LLM is given a Python REPL environment and can programmatically examine, decompose, and recursively call itself (or sub-LLM instances) on portions of its input. Unlike traditional agents that operate turn-by-turn with discrete tool calls, an RLM writes and executes code in a persistent REPL until it signals completion.

**REPL (Read-Eval-Print Loop):**
The persistent Python execution environment at the heart of an RLM session. The LLM generates Python code, the REPL executes it, and the output feeds back as the next input. State persists across turns within a session. The REPL is where the LLM's "reasoning" happens -- it can define variables, import modules, call sub-LLMs, and signal completion.

**Orchestrator:**
The outer agent loop that manages an RLM conversation. It handles user I/O, dispatches to the RLM, enforces recursion depth and round limits, triggers context compaction, and manages model configuration. The Orchestrator is what users invoke via the CLI or library API.

**Session:**
A single RLM conversation, consisting of one user prompt and the full tree of REPL interactions and sub-LLM calls that follow. A Session has a single root REPL and a bounded tree of child REPLs spawned by sub-LLM calls. A Session is interactive: the user can steer mid-execution, cancel cleanly, and review the full Trajectory after completion.

**Sub-LLM (sub_llm):**
The recursion primitive -- a callable exposed inside the REPL that launches a fresh child Session. The child gets its own REPL and a snippet of the parent's context. Results propagate back to the parent REPL. Sub-LLM calls can execute in parallel.

**Compaction:**
The process of summarizing REPL history when accumulated output approaches the model's context limit. Uses an LLM to produce a compact summary that preserves important intermediate results and discards verbose output.

**Profile:**
A named configuration preset that bundles model choice, recursion limits, and environment settings. Users switch profiles via the active_profile config key or --profile CLI flag. Examples: "fast" (local model, low depth), "balanced" (cloud model, moderate depth), "powerful" (best model, high depth).

**Environment (Sandbox):**
The execution context for REPL code. Three tiers: `local` (in-process Python exec, fastest, no isolation), `Docker` (containerized execution), and cloud sandboxes like Modal/E2B/Daytona (stubbed). The REPL runs arbitrary Python code within the active Environment.

**Trajectory:**
The complete execution log of a Session -- every code snippet the LLM generated, every REPL output, every sub-LLM call and its results. Written to disk for observability and rendered in the terminal in verbose mode.

**Search:**
A tool exposed in the REPL for finding content across the codebase. Starts as grep-backed; the interface is designed to be swapped for semantic/vector search without changing the agent code.

**Index:**
A pre-built representation of the codebase that enables efficient search. Generation happens at session start. Currently a file tree listing; the architecture supports upgrading to embeddings later.

**Complete (complete):**
A callable exposed in the REPL that signals the LLM is done. The session terminates and the value is returned to the Orchestrator.

**Dry Run:**
An execution mode where all file modifications are written to a temporary directory instead of the working tree. The user reviews the diff before applying. Contrast with the default mode where files are modified in place.

**Interactive Mode:**
A CLI mode where the user enters a persistent Session with the agent. The user issues the initial prompt, observes the agent's progress, can steer mid-execution with follow-up messages injected into the REPL, and can cancel cleanly with Ctrl+C.
