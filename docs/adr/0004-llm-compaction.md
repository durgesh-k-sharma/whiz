# ADR-0004: LLM-Based Compaction for Context Management

When the REPL history exceeds a token threshold, Whiz uses an LLM to summarize the accumulated state, preserving important intermediate results and discarding verbose output. The summary replaces the history in the context window.

Alternative considered: naive truncation (keep last N turns). Rejected because important intermediate results (file contents, search results, computed values) could be discarded even if they're relevant to the final answer. LLM summarization is more expensive per compaction event but preserves semantic content.
