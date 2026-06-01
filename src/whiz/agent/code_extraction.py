"""Shared code extraction from LLM responses."""
from __future__ import annotations


def extract_code(content: str) -> str | None:
    """Extract executable Python code from an LLM response.

    Handles:
    - Markdown code blocks (```...```)
    - Raw Python code
    - Plain text (wrapped in complete() to end the session)
    """
    content = content.strip()
    if not content:
        return None

    # If the response is wrapped in markdown code blocks, extract from them
    if "```" in content:
        blocks = []
        in_block = False
        block_lines = []
        for line in content.split("\n"):
            if line.strip().startswith("```"):
                if in_block:
                    blocks.append("\n".join(block_lines))
                    block_lines = []
                    in_block = False
                else:
                    in_block = True
            elif in_block:
                block_lines.append(line)
        if blocks:
            return blocks[-1].strip()

    # Check if the whole response is valid Python
    try:
        compile(content, "<llm>", "exec")
        return content
    except SyntaxError:
        pass

    # Try to find a Python-like line
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            try:
                compile(line, "<llm>", "exec")
                return line
            except SyntaxError:
                continue

    # Plain text answer -- wrap in complete() so the session ends
    escaped = content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'complete("{escaped[:500]}")'
