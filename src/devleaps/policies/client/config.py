"""
Configuration system for agent policies.

Supports loading configuration from:
1. User home directory: ~/.agent-policies/config.json
2. Project directory: .agent-policies/config.json

Configurations are merged with project-level settings taking precedence over home-level.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages configuration loading and merging from multiple levels."""

    DEFAULT_CONFIG = {
        "bundles": [],
        "editor": "claude-code",
        "server_url": "http://localhost:8338",
    }

    @staticmethod
    def _load_config_file(path: Path) -> Dict[str, Any]:
        """Load a single configuration file, return empty dict if not found."""
        if not path.exists():
            return {}

        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load config from {path}: {e}")
            return {}

    @staticmethod
    def _merge_configs(home_config: Dict[str, Any], project_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge home and project configs, with project taking precedence."""
        merged = ConfigManager.DEFAULT_CONFIG.copy()

        # Merge home config
        merged.update(home_config)

        # Merge project config (overrides home config)
        merged.update(project_config)

        return merged

    @classmethod
    def load_config(cls, project_root: Optional[str] = None) -> Dict[str, Any]:
        """
        Load and merge configuration from home and project directories.

        Args:
            project_root: Root directory of the project. If None, uses current directory.

        Returns:
            Merged configuration dictionary.
        """
        if project_root is None:
            project_root = os.getcwd()

        # Load home directory config
        home_config_path = Path.home() / ".agent-policies" / "config.json"
        home_config = cls._load_config_file(home_config_path)

        # Load project directory config
        project_config_path = Path(project_root) / ".agent-policies" / "config.json"
        project_config = cls._load_config_file(project_config_path)

        # Merge and return
        return cls._merge_configs(home_config, project_config)

    @staticmethod
    def get_enabled_bundles(config: Optional[Dict[str, Any]] = None) -> list:
        """Get list of enabled bundles from config."""
        if config is None:
            config = ConfigManager.load_config()
        return config.get("bundles", [])

    @staticmethod
    def get_editor(config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Get editor preference from config."""
        if config is None:
            config = ConfigManager.load_config()
        return config.get("editor")

    @staticmethod
    def get_server_url(config: Optional[Dict[str, Any]] = None) -> str:
        """Get server URL from config."""
        if config is None:
            config = ConfigManager.load_config()
        return config.get("server_url", "http://localhost:8338")

    @staticmethod
    def ensure_config_directories() -> None:
        """Ensure configuration directories exist."""
        home_config_dir = Path.home() / ".agent-policies"
        home_config_dir.mkdir(parents=True, exist_ok=True)

        project_config_dir = Path.cwd() / ".agent-policies"
        project_config_dir.mkdir(parents=True, exist_ok=True)
