"""Tests for configuration system."""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

from devleaps.policies.client.config import ConfigManager


def test_load_valid_config_file():
    """Loading a valid config file returns parsed JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {"bundles": ["python-quality"], "editor": "cursor"}
        json.dump(config, f)
        f.flush()

        try:
            result = ConfigManager._load_config_file(Path(f.name))
            assert result == config
        finally:
            os.unlink(f.name)


def test_merge_project_overrides_home():
    """Project config takes precedence over home config."""
    home_config = {"bundles": ["python-quality"], "editor": "vscode"}
    project_config = {"bundles": ["git-workflow"], "editor": "cursor"}
    result = ConfigManager._merge_configs(home_config, project_config)
    assert result["bundles"] == ["git-workflow"]
    assert result["editor"] == "cursor"


def test_get_enabled_bundles():
    """get_enabled_bundles returns bundles from config."""
    config = {"bundles": ["python-quality", "git-workflow"]}
    result = ConfigManager.get_enabled_bundles(config)
    assert result == ["python-quality", "git-workflow"]


def test_get_editor():
    """get_editor returns editor preference from config."""
    config = {"editor": "cursor"}
    result = ConfigManager.get_editor(config)
    assert result == "cursor"
