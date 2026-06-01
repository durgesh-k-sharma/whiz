# ADR-0003: In-Process Local REPL as Default Sandbox

The default REPL environment runs code via Python `exec()` in the same process as the host agent. This is fast, simple, and has zero setup cost. It also means the LLM has full access to the host machine -- filesystem, network, environment variables.

We chose this as the default because Whiz is a developer tool running on the user's own machine against their own codebase. The user already has full access to their machine; the agent is an extension of their intent. Docker and cloud sandboxes are available as opt-in for users who need isolation.

Alternative considered: defaulting to Docker for safety. Rejected because it adds significant setup friction (Docker must be installed and running), increases latency per tool call (container startup), and developer CLI tools in practice expect host access (git, package managers, etc.).
