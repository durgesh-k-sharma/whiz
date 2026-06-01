# Whiz Usage Examples

## One-shot mode

```bash
# Basic usage
export OPENAI_API_KEY=sk-***
whiz run "find all TODO comments in the codebase"

# With profile
whiz --profile powerful "analyze the architecture of this project"

# Dry run (preview changes)
whiz run --dry-run "refactor the auth module"

# Auto-commit changes
whiz run --auto-commit "add type hints to all functions"
```

## Interactive mode

```bash
# Start interactive session
whiz interactive "explore thefind all unused imports"

# Mid-session steering: typefollow-up messages after # the agent starts working
# > focus on the src/ directory only
# > stop
```

## Library API

```python
from whiz import Session
from whiz.models import OpenAIModel

# Basic usage
session = Session(
    model=OpenAIModel(model="gpt-4o", api_key="sk-***"),
    project_root="/path/to/project",
    verbose=True,
)
result = session.run("refactor the authentication module")
print(f"Result: {result.value}")
print(f"Rounds: {result.rounds}")

# With options
result = Session(
    model=OpenAIModel(model="gpt-4o", api_key="sk-***"),
    max_rounds=50,
    max_recursion_depth=3,
    dry_run=True,
).run("analyze all test files")

# Async with steering
import asyncio

async def main():
    session = Session(model=OpenAIModel(model="gpt-4o", api_key="sk-***"))
    result = await session.arun("explore the codebase")
    print(result.value)

asyncio.run(main())
```

## Working with Ollama (local models)

```yaml
# ~/.whiz/config.yaml
profiles:
  local:
    backend: ollama
    model: llama3
    sub_model: ollama/llama3
active_profile: local
```

```bash
whiz run "summarize the project structure"
```
