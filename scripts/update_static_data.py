"""Refresh normalized name-day and theme-day source snapshots."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Final
from urllib.request import Request, urlopen

COMPONENT_DIRECTORY: Final = (
    Path(__file__).resolve().parents[1] / "custom_components" / "swedish_calendar_plus"
)
sys.path.insert(0, str(COMPONENT_DIRECTORY))

from source_parsers import (  # noqa: E402
    NAME_DAY_URL,
    THEME_DAY_URL,
    merge_theme_history,
    normalize_name_days,
    normalize_theme_days,
)

DATA_DIRECTORY: Final = COMPONENT_DIRECTORY / "data"


def _download(url: str) -> str:
    request = Request(  # noqa: S310
        url,
        headers={"User-Agent": "swedish-calendar-plus-data/1"},
    )
    with urlopen(request, timeout=30) as response:  # noqa: S310
        return response.read().decode("utf-8")


def _source_content_changed(existing: object, candidate: object) -> bool:
    """Return whether source content changed, ignoring the retrieval timestamp."""
    if not isinstance(existing, dict) or not isinstance(candidate, dict):
        return existing != candidate
    existing_content = {
        key: value for key, value in existing.items() if key != "retrieved_at"
    }
    candidate_content = {
        key: value for key, value in candidate.items() if key != "retrieved_at"
    }
    return existing_content != candidate_content


def _write_json_if_changed(filename: str, payload: object) -> bool:
    """Write a dataset only when content other than retrieved_at changed."""
    path = DATA_DIRECTORY / filename
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if not _source_content_changed(existing, payload):
            return False
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )
    return True


def update_name_days(retrieved_at: str) -> None:
    """Download and normalize Svenska Akademien's current name-day calendar."""
    normalized = normalize_name_days(json.loads(_download(NAME_DAY_URL)), retrieved_at)
    _write_json_if_changed("name_days.json", normalized)


def update_theme_days(retrieved_at: str) -> None:
    """Download and normalize the published Temadagar annual calendar."""
    current = normalize_theme_days(_download(THEME_DAY_URL), retrieved_at)
    existing_path = DATA_DIRECTORY / "theme_days.json"
    existing = (
        json.loads(existing_path.read_text(encoding="utf-8"))
        if existing_path.exists()
        else {"days": [], "calendar_years": []}
    )
    merged = merge_theme_history(existing, current, retrieved_at)
    _write_json_if_changed("theme_days.json", merged)


def main() -> None:
    """Refresh both static source snapshots."""
    retrieved_at = datetime.now(tz=UTC).date().isoformat()
    update_name_days(retrieved_at)
    update_theme_days(retrieved_at)


if __name__ == "__main__":
    main()
