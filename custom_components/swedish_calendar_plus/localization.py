"""Runtime localization for generated calendar content."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import cast

_translations: dict[str, dict[str, object]] = {}


def load_translations() -> None:
    """Load bundled translation files outside the event loop."""
    directory = files(__package__).joinpath("translations")
    for path in directory.iterdir():
        if path.name.endswith(".json"):
            _translations[path.name.removesuffix(".json")] = cast(
                "dict[str, object]",
                json.loads(path.read_text(encoding="utf-8")),
            )


def translate(language: str, key: str) -> str:
    """Translate a common runtime key with English fallback."""
    for candidate in (language, "en"):
        value: object = _translations.get(candidate, {}).get("common", {})
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                value = None
                break
            value = cast("dict[str, object]", value)[part]
        if isinstance(value, str):
            return value
    return key
