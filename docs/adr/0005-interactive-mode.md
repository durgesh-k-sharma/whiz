# ADR-0005: Interactive CLI with Mid-Session Steering as Day-One Feature

Whiz provides an interactive CLI mode (`whiz` with no subcommand) where the user enters a persistent Session. After the initial prompt, the user can steer mid-execution by sending follow-up messages that get injected into the REPL as `_user_steer` variables. Ctrl+C cancels cleanly, killing active sub-calls and writing the partial Trajectory to disk.

One-shot mode (`whiz run "..."`) exits after the first Session completes.

Steering is event-driven: the Orchestrator relays user messages to the active REPL between turns. The LLM sees the steer on its next REPL round and adjusts course. This requires the Orchestrator to be non-blocking during REPL execution, using async I/O to listen for user input.

Alternative considered: sequential one-shot only, steering as a stretch goal. Rejected because steering is a core part of the developer workflow -- a coding agent that can't be corrected mid-task is significantly less useful.
