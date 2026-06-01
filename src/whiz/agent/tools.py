"""Shared tool injection for REPL environments."""
from __future__ import annotations

from pathlib import Path

from whiz.repl.core import LocalREPL
from whiz.tools.search import SearchTool
from whiz.tools.filesystem import ReadFilesTool, EditFileTool, RunTestsTool
from whiz.agent.recursion import create_sub_llm_callable
from whiz.agent.loop_base import SubLLMManager


def inject_tools(
    repl: LocalREPL,
    model,
    project_root: Path,
    recursion_mgr: SubLLMManager,
    max_rounds: int = 100,
) -> None:
    """Inject all tool callables into the REPL namespace.

    Creates a fresh set of tool instances and wires them into the REPL.
    The `complete()` function sets _done/_done_value flags in the namespace
    to signal session completion.
    """
    def complete(value):
        repl._namespace["_done"] = True
        repl._namespace["_done_value"] = value
        return value

    sub_llm = create_sub_llm_callable(
        model=model,
        project_root=project_root,
        recursion_mgr=recursion_mgr,
        max_rounds=min(max_rounds, 50),
    )

    search_tool = SearchTool(project_root=project_root)
    read_tool = ReadFilesTool(project_root=project_root)
    edit_tool = EditFileTool(project_root=project_root)
    run_tests_tool = RunTestsTool(project_root=project_root)

    repl._namespace["search"] = search_tool.search
    repl._namespace["read_files"] = read_tool.read_files
    repl._namespace["edit_file"] = edit_tool.edit_file
    repl._namespace["run_tests"] = run_tests_tool.run_tests
    repl._namespace["sub_llm"] = sub_llm
    repl._namespace["complete"] = complete
