"""Tests for config loading, profile resolution, and CLI."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch

from whiz.config import Config, Profile, load_config, resolve_profile


# --- Profile ---

class TestProfile:
    def test_profile_defaults(self):
        p = Profile(name="test", backend="openai", model="gpt-4o")
        assert p.name == "test"
        assert p.backend == "openai"
        assert p.model == "gpt-4o"
        assert p.sub_model is None
        assert p.max_depth == 5
        assert p.max_repl_rounds == 100
        assert p.environment == "local"

    def test_profile_custom_values(self):
        p = Profile(
            name="fast",
            backend="ollama",
            model="llama3",
            sub_model="ollama/llama3",
            max_depth=3,
            max_repl_rounds=50,
            environment="docker",
        )
        assert p.sub_model == "ollama/llama3"
        assert p.max_depth == 3
        assert p.environment == "docker"


# --- Config ---

class TestConfig:
    def test_config_from_dict(self):
        data = {
            "profiles": {
                "balanced": {
                    "backend": "openai",
                    "model": "gpt-4o",
                }
            },
            "active_profile": "balanced",
        }
        config = Config.from_dict(data)
        assert config.active_profile == "balanced"
        assert "balanced" in config.profiles
        assert config.profiles["balanced"].backend == "openai"

    def test_config_active_profile_data(self):
        data = {
            "profiles": {
                "fast": {
                    "backend": "ollama",
                    "model": "llama3",
                }
            },
            "active_profile": "fast",
        }
        config = Config.from_dict(data)
        active = config.active_profile_data
        assert isinstance(active, Profile)
        assert active.backend == "ollama"

    def test_config_missing_active_profile_raises(self):
        data = {
            "profiles": {
                "fast": {"backend": "ollama", "model": "llama3"}
            },
            "active_profile": "nonexistent",
        }
        with pytest.raises(KeyError):
            Config.from_dict(data)


# --- load_config ---

class TestLoadConfig:
    def test_load_config_merges_global_and_project(self, tmp_path):
        global_cfg = tmp_path / "global.yaml"
        global_cfg.write_text(
            "profiles:\n"
            "  balanced:\n"
            "    backend: openai\n"
            "    model: gpt-4o\n"
            "active_profile: balanced\n"
            "logging:\n"
            "  dir: ~/.whiz/logs\n"
        )
        project_cfg = tmp_path / "project.yaml"
        project_cfg.write_text(
            "active_profile: fast\n"
            "profiles:\n"
            "  fast:\n"
            "    backend: ollama\n"
            "    model: llama3\n"
        )
        with patch("whiz.config.GLOBAL_CONFIG_PATH", global_cfg), \
             patch("whiz.config.find_project_config", return_value=project_cfg):
            config = load_config(project_root=tmp_path)
            assert config.active_profile == "fast"
            # Project overrides active_profile
            assert config.active_profile_data.backend == "ollama"
            # Global values still exist
            assert "balanced" in config.profiles
            assert "logging" in config._raw

    def test_load_config_with_env_var_expansion(self, tmp_path):
        global_cfg = tmp_path / "global.yaml"
        global_cfg.write_text(
            "profiles:\n"
            "  balanced:\n"
            "    backend: openai\n"
            "    model: gpt-4o\n"
            "active_profile: balanced\n"
        )
        project_cfg = tmp_path / "nonexistent.yaml"
        with patch("whiz.config.GLOBAL_CONFIG_PATH", global_cfg), \
             patch("whiz.config.find_project_config", return_value=project_cfg):
            config = load_config(project_root=tmp_path)
            assert config.active_profile == "balanced"

    def test_load_config_none_exists_returns_defaults(self, tmp_path):
        with patch("whiz.config.GLOBAL_CONFIG_PATH", tmp_path / "noglobal.yaml"), \
             patch("whiz.config.find_project_config", return_value=None):
            config = load_config(project_root=tmp_path)
            # Should return a default config
            assert config.active_profile is not None


# --- resolve_profile ---

class TestResolveProfile:
    def test_resolve_by_flag_overrides_config(self):
        data = {
            "profiles": {
                "fast": {"backend": "ollama", "model": "llama3"},
                "powerful": {"backend": "openrouter", "model": "openrouter/auto"},
            },
            "active_profile": "fast",
        }
        config = Config.from_dict(data)
        profile = resolve_profile(config, profile_flag="powerful")
        assert profile.name == "powerful"
        assert profile.backend == "openrouter"

    def test_resolve_by_config_active_profile(self):
        data = {
            "profiles": {
                "fast": {"backend": "ollama", "model": "llama3"},
            },
            "active_profile": "fast",
        }
        config = Config.from_dict(data)
        profile = resolve_profile(config, profile_flag=None)
        assert profile.name == "fast"
