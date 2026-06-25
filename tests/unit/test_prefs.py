from unittest.mock import patch

from omni_wells.prefs import DEFAULTS, load, save


def test_load_returns_defaults_when_no_file(tmp_path):
    with patch("omni_wells.prefs.PREFS_FILE", tmp_path / "prefs.json"):
        result = load()
        assert result == DEFAULTS


def test_save_and_load(tmp_path):
    prefs_file = tmp_path / "prefs.json"
    with patch("omni_wells.prefs.PREFS_FILE", prefs_file):
        save({"theme": "dark", "decimal": ","})
        result = load()
        assert result["theme"] == "dark"
        assert result["decimal"] == ","


def test_save_merges_with_defaults(tmp_path):
    prefs_file = tmp_path / "prefs.json"
    with patch("omni_wells.prefs.PREFS_FILE", prefs_file):
        save({"theme": "dark"})
        result = load()
        assert result["theme"] == "dark"
        assert result["decimal"] == DEFAULTS["decimal"]


def test_save_creates_directory(tmp_path):
    prefs_file = tmp_path / "nested" / "dir" / "prefs.json"
    with patch("omni_wells.prefs.PREFS_FILE", prefs_file):
        save({"theme": "light"})
        assert prefs_file.exists()


def test_load_with_corrupted_file(tmp_path):
    prefs_file = tmp_path / "prefs.json"
    prefs_file.write_text("invalid json {{{")
    with patch("omni_wells.prefs.PREFS_FILE", prefs_file):
        result = load()
        assert result == DEFAULTS
