"""Configuration loading, profiles, and resolution for Whiz."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


GLOBAL_CONFIG_PATH = Path.home() / ".whiz" / "config.yaml"
PROJECT_CONFIG_NAME = ".whiz/config.yaml"

DEFAULT_PROFILES = {
    "balanced": {
        "backend": "openai",
        "model": "gpt-4o",
        "sub_model": None,
        "recursion": {"max_depth": 5, "max_repl_rounds": 100},
        "environment": "local",
    },
    "fast": {
        "backend": "ollama",
        "model": "llama3",
        "sub_model": "ollama/llama3",
        "recursion": {"max_depth": 3, "max_repl_rounds": 50},
        "environment": "local",
    },
    "powerful": {
        "backend": "openrouter",
        "model": "openrouter/auto",
        "sub_model": None,
        "recursion": {"max_depth": 10, "max_repl_rounds": 200},
        "environment": "local",
    },
}


@dataclass
class Profile:
    name: str
    backend: str
    model: str
    sub_model: str | None = None
    max_depth: int = 5
    max_repl_rounds: int = 100
    environment: str = "local"

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> Profile:
        recursion = data.get("recursion", {})
        return cls(
            name=name,
            backend=data["backend"],
            model=data["model"],
            sub_model=data.get("sub_model"),
            max_depth=recursion.get("max_depth", 5),
            max_repl_rounds=recursion.get("max_repl_rounds", 100),
            environment=data.get("environment", "local"),
        )


@dataclass
class Config:
    active_profile: str
    profiles: dict[str, Profile]
    _raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        profiles_data = data.get("profiles", {})
        profiles = {
            name: Profile.from_dict(name, pdata)
            for name, pdata in profiles_data.items()
        }
        active = data.get("active_profile", "balanced")
        if active not in profiles:
            raise KeyError(
                f"Active profile '{active}' not found in profiles: {list(profiles)}"
            )
        return cls(
            active_profile=active,
            profiles=profiles,
            _raw=data,
        )

    @property
    def active_profile_data(self) -> Profile:
        return self.profiles[self.active_profile]


def _load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return _expand_env_vars(data)


def _expand_env_vars(obj: Any) -> Any:
    if isinstance(obj, str):
        return os.path.expandvars(obj)
    if isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_env_vars(v) for v in obj]
    return obj


def find_project_config(project_root: Path) -> Path | None:
    candidate = project_root / PROJECT_CONFIG_NAME
    if candidate.exists():
        return candidate
    return None


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(project_root: Path | None = None) -> Config:
    # Start with defaults
    raw: dict[str, Any] = {
        "profiles": dict(DEFAULT_PROFILES),
        "active_profile": "balanced",
    }

    # Merge global config
    global_data = _load_yaml(GLOBAL_CONFIG_PATH)
    if global_data:
        raw = _deep_merge(raw, global_data)

    # Merge project config
    if project_root:
        project_path = find_project_config(project_root)
        if project_path:
            project_data = _load_yaml(project_path)
            if project_data:
                raw = _deep_merge(raw, project_data)

    return Config.from_dict(raw)


def resolve_profile(config: Config, profile_flag: str | None = None) -> Profile:
    name = profile_flag if profile_flag else config.active_profile
    if name not in config.profiles:
        raise KeyError(
            f"Profile '{name}' not found. Available: {list(config.profiles)}"
        )
    return config.profiles[name]
