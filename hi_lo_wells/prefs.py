import json
from pathlib import Path

PREFS_FILE = Path.home() / ".config" / "hi-lo-wells" / "prefs.json"

DEFAULTS = {
    "decimal": ".",
    "thousands": "",
    "csvsep": ",",
    "theme": "light",
    "last_import_dir": str(Path.home()),
    "last_download_dir": str(Path.home() / "Downloads"),
}


def load() -> dict:
    try:
        return {**DEFAULTS, **json.loads(PREFS_FILE.read_text())}
    except Exception:
        return DEFAULTS.copy()


def save(data: dict) -> None:
    PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    current = load()
    current.update(data)
    PREFS_FILE.write_text(json.dumps(current))
