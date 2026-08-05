"""Tests for config_manager module."""
import json
import tempfile
from pathlib import Path

from emailsenderpro.core.config_manager import ConfigManager


def test_config_save_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.json"
        cm = ConfigManager(config_path)
        cm.set("email", "test@example.com")
        cm.set("port", 587)
        cm.save()

        cm2 = ConfigManager(config_path)
        assert cm2.get("email") == "test@example.com"
        assert cm2.get("port") == 587


def test_config_has_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.json"
        cm = ConfigManager(config_path)
        assert not cm.has_config()
        cm.set("email", "test@example.com")
        assert cm.has_config()
