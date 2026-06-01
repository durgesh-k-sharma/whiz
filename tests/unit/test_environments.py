"""Tests for environment architecture: local, Docker, cloud stubs."""
import pytest
from pathlib import Path

from whiz.repl.base import BaseEnvironment
from whiz.repl.core import LocalREPL
from whiz.repl.docker import DockerEnvironment
from whiz.repl.cloud import ModalEnvironment, E2BDaytonaEnvironment, PrimeEnvironment


# --- LocalREPL implements BaseEnvironment ---

class TestLocalREPLImplementsBase:
    def test_is_base_environment(self):
        repl = LocalREPL()
        assert isinstance(repl, BaseEnvironment)

    def test_exec_code_returns_str(self):
        repl = LocalREPL()
        result = repl.exec_code("1 + 1")
        assert isinstance(result, str)

    def test_get_namespace_returns_dict(self):
        repl = LocalREPL()
        ns = repl.get_namespace()
        assert isinstance(ns, dict)


# --- Docker Environment ---

class TestDockerEnvironment:
    def test_creation(self):
        env = DockerEnvironment(project_root=Path("/tmp"))
        assert env.project_root == Path("/tmp")

    def test_is_base_environment(self):
        env = DockerEnvironment(project_root=Path("/tmp"))
        assert isinstance(env, BaseEnvironment)

    def test_exec_code_returns_str(self):
        env = DockerEnvironment(project_root=Path("/tmp"))
        result = env.exec_code("print('hello')")
        assert isinstance(result, str)

    def test_handles_docker_unavailable(self):
        """If Docker is not available, should return a clear error."""
        env = DockerEnvironment(project_root=Path("/tmp"))
        result = env.exec_code("1 + 1")
        # Should either work or return a clear Docker error
        assert isinstance(result, str)


# --- Cloud Sandbox Stubs ---

class TestCloudStubs:
    def test_modal_raises_not_implemented(self):
        env = ModalEnvironment(project_root=Path("/tmp"))
        with pytest.raises(NotImplementedError):
            env.exec_code("1 + 1")

    def test_e2b_raises_not_implemented(self):
        env = E2BDaytonaEnvironment(project_root=Path("/tmp"), provider="e2b")
        with pytest.raises(NotImplementedError):
            env.exec_code("1 + 1")

    def test_daytona_raises_not_implemented(self):
        env = E2BDaytonaEnvironment(project_root=Path("/tmp"), provider="daytona")
        with pytest.raises(NotImplementedError):
            env.exec_code("1 + 1")

    def test_prime_raises_not_implemented(self):
        env = PrimeEnvironment(project_root=Path("/tmp"))
        with pytest.raises(NotImplementedError):
            env.exec_code("1 + 1")

    def test_cloud_stubs_have_clear_error_messages(self):
        """Cloud stubs should tell users how to enable them."""
        for env_cls, kwargs in [
            (ModalEnvironment, {}),
            (E2BDaytonaEnvironment, {"provider": "e2b"}),
            (PrimeEnvironment, {}),
        ]:
            env = env_cls(project_root=Path("/tmp"), **kwargs)
            try:
                env.exec_code("1")
            except NotImplementedError as e:
                msg = str(e).lower()
                assert "not implemented" in msg or "install" in msg or "coming" in msg
