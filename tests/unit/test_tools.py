"""Tests for codebase index and filesystem tools."""
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from whiz.tools.search import SearchTool
from whiz.tools.filesystem import ReadFilesTool, EditFileTool, RunTestsTool
from whiz.context.indexer import CodebaseIndex


# --- CodebaseIndex ---

class TestCodebaseIndex:
    def test_index_scans_files(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def add(): pass")
        (tmp_path / "README.md").write_text("# Project")
        index = CodebaseIndex.from_root(tmp_path)
        assert "main.py" in index.file_tree
        assert "utils.py" in index.file_tree
        assert "README.md" in index.file_tree

    def test_index_ignores_hidden_dirs(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("git config")
        (tmp_path / "main.py").write_text("x = 1")
        index = CodebaseIndex.from_root(tmp_path)
        assert ".git" not in index.file_tree
        assert "main.py" in index.file_tree

    def test_index_ignores_pycache(self, tmp_path):
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "main.cpython-314.pyc").write_text("bytecode")
        (tmp_path / "main.py").write_text("x = 1")
        index = CodebaseIndex.from_root(tmp_path)
        assert "__pycache__" not in index.file_tree

    def test_index_reads_readme(self, tmp_path):
        (tmp_path / "README.md").write_text("# My Project\n\nDescription here.")
        index = CodebaseIndex.from_root(tmp_path)
        assert "# My Project" in index.readme

    def test_index_no_readme(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1")
        index = CodebaseIndex.from_root(tmp_path)
        assert index.readme == ""

    def test_index_readme_truncated(self, tmp_path):
        long_readme = "\n".join(f"Line {i}" for i in range(500))
        (tmp_path / "README.md").write_text(long_readme)
        index = CodebaseIndex.from_root(tmp_path)
        assert len(index.readme.split("\n")) <= 210  # some buffer for truncation message

    def test_index_scans_subdirectories(self, tmp_path):
        sub = tmp_path / "src" / "core"
        sub.mkdir(parents=True)
        (sub / "logic.py").write_text("# logic")
        (tmp_path / "main.py").write_text("x = 1")
        index = CodebaseIndex.from_root(tmp_path)
        assert "src" in index.file_tree

    def test_to_repl_variables(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1")
        (tmp_path / "README.md").write_text("# Title")
        index = CodebaseIndex.from_root(tmp_path)
        vars = index.to_repl_variables()
        assert "file_tree" in vars
        assert "readme" in vars
        assert "project_root" in vars
        assert "main.py" in vars["file_tree"]
        assert "# Title" in vars["readme"]


# --- SearchTool ---

class TestSearchTool:
    def test_grep_search(self, tmp_path):
        (tmp_path / "auth.py").write_text("def authenticate(user, password):\n    pass")
        (tmp_path / "main.py").write_text("import authenticate")
        base_url = "https://api.example.com"
        tool = SearchTool(project_root=tmp_path, backend="grep", base_url=base_url)
        result = tool.search("authenticate")
        assert "auth.py" in result

    def test_search_no_results(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1")
        base_url = "https://api.example.com"
        tool = SearchTool(project_root=tmp_path, backend="grep", base_url=base_url)
        result = tool.search("nonexistent")
        assert result == "" or "no results" in result.lower()

    def test_search_returns_snippets(self, tmp_path):
        (tmp_path / "file.py").write_text("line1\nTODO: fix this\nline3")
        base_url = "https://api.example.com"
        tool = SearchTool(project_root=tmp_path, backend="grep", base_url=base_url)
        result = tool.search("TODO")
        assert "TODO" in result


# --- ReadFilesTool ---

class TestReadFilesTool:
    def test_read_single_file(self, tmp_path):
        (tmp_path / "hello.py").write_text("print('hello')")
        tool = ReadFilesTool(project_root=tmp_path)
        result = tool.read_files(["hello.py"])
        assert "hello" in result

    def test_read_multiple_files(self, tmp_path):
        (tmp_path / "a.py").write_text("file a")
        (tmp_path / "b.py").write_text("file b")
        tool = ReadFilesTool(project_root=tmp_path)
        result = tool.read_files(["a.py", "b.py"])
        assert "file a" in result
        assert "file b" in result

    def test_read_missing_file(self, tmp_path):
        tool = ReadFilesTool(project_root=tmp_path)
        result = tool.read_files(["nonexistent.py"])
        assert "not found" in result.lower() or "error" in result.lower()

    def test_path_traversal_blocked(self, tmp_path):
        tool = ReadFilesTool(project_root=tmp_path)
        result = tool.read_files(["../../etc/passwd"])
        assert "not allowed" in result.lower() or "outside" in result.lower()


# --- EditFileTool ---

class TestEditFileTool:
    def test_edit_existing_file(self, tmp_path):
        (tmp_path / "target.py").write_text("old content")
        tool = EditFileTool(project_root=tmp_path)
        tool.edit_file("target.py", "new content")
        assert (tmp_path / "target.py").read_text() == "new content"

    def test_edit_creates_file(self, tmp_path):
        tool = EditFileTool(project_root=tmp_path)
        tool.edit_file("new_file.py", "brand new")
        assert (tmp_path / "new_file.py").read_text() == "brand new"

    def test_path_traversal_blocked(self, tmp_path):
        tool = EditFileTool(project_root=tmp_path)
        result = tool.edit_file("../../etc/passwd", "evil")
        assert "not allowed" in result.lower() or "outside" in result.lower()


# --- RunTestsTool ---

class TestRunTestsTool:
    def test_run_pytest(self, tmp_path):
        (tmp_path / "test_sample.py").write_text(
            "def test_pass():\n    assert 1 + 1 == 2\n"
        )
        tool = RunTestsTool(project_root=tmp_path)
        result = tool.run_tests()
        # Should not error
        assert "error" not in result.lower() or "passed" in result.lower()

    def test_run_tests_no_test_files(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1")
        tool = RunTestsTool(project_root=tmp_path)
        result = tool.run_tests()
        assert result  # should return something meaningful
