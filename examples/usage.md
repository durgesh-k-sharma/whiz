# Whiz Usage Examples

## One-shot mode

```bash
# Basic usage with OpenRouter free tier
export OPENROUTER_API_KEY="sk-or-..."
whiz run "find all TODO comments in the codebase"

# With specific profile
whiz run --profile or-claude "analyze the architecture of this project"
whiz run --profile or-gpt4o "summarize this code"

# Auto-commit changes
whiz run --auto-commit "add type hints to all functions"

# Limit rounds for quick tasks
whiz run --max-rounds 5 "what files handle routing?"
```

## Interactive mode

```bash
# Start interactive session
whiz interactive "explore the codebase and find all unused imports"

# Mid-session steering: type follow-up messages after the agent starts working
# > focus on the src/ directory only
# > stop
```

## Library API

```python
from whiz import Session
from whiz.models import OpenAIModel

# Basic usage
session = Session(
    model=OpenAIModel(model="gpt-4o", key="..."),
    project_root="/path/to/project",
    verbose=True,
)
result = session.run("refactor the authentication module")
print(f"Result: {result.value}")
print(f"Rounds: {result.rounds}")

# With options
result = Session(
    model=OpenAIModel(model="gpt-4o", key="..."),
    max_rounds=50,
    max_recursion_depth=3,
).run("analyze all test files")

# Async with steering support
import asyncio

async def main():
    session = Session(model=OpenAIModel(model="gpt-4o", key="..."))
    result = await session.arun("explore the codebase")
    print(result.value)

asyncio.run(main())
```

## Working with Ollama (local models)

```yaml
# ~/.whiz/config.yaml
profiles:
  ollama:
    backend: ollama
    model: llama3
    recursion:
      max_depth: 3
      max_repl_rounds: 50
active_profile: ollama
```

```bash
whiz run "summarize the project structure"
```

## Using OpenRouter

```bash
export OPENROUTER_API_KEY="sk-or-..."

# Free tier (default profile)
whiz run "your task"

# Specific model via OpenRouter
whiz run --profile or-claude "complex reasoning task"
whiz run --profile or-gpt4o "another task"

# List available free models at https://openrouter.ai/models?price=free
```
