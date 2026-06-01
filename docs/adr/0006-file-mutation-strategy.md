# ADR-0006: File Mutation Strategy -- In-Place by Default, Dry-Run Via Flag

Whiz modifies files in the working directory by default, like any developer tool (git, sed, an editor). The user reviews changes with `git diff` after the session. `--dry-run` writes all modifications to a temporary directory and shows a unified diff without touching the working tree. `--auto-commit` automatically runs `git commit` with an LLM-generated commit message after the session completes.

Alternative considered: always writing to a temp dir and requiring explicit apply. Rejected because it adds friction to the primary workflow. Developers expect CLI tools that operate on their working tree to modify files in place. Dry-run is available for users who want the safety net.
