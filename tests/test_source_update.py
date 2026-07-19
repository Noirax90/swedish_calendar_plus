"""Tests for runtime source update validation and history."""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.swedish_calendar_plus.const import DOMAIN
from custom_components.swedish_calendar_plus.source_parsers import (
    merge_theme_history,
    normalize_name_days,
)
from custom_components.swedish_calendar_plus.source_update import (
    SOURCE_UPDATE_ISSUE_ID,
    SourceResponseTooLargeError,
    SourceUpdater,
    _async_read_limited,
    _dataset_metadata,
)


class _FakeContent:
    def __init__(self, chunks: tuple[bytes, ...]) -> None:
        self._chunks = chunks

    async def iter_chunked(self, _size: int):  # noqa: ANN202
        for chunk in self._chunks:
            yield chunk


class _FakeResponse:
    def __init__(
        self,
        chunks: tuple[bytes, ...],
        content_length: int | None = None,
    ) -> None:
        self.content = _FakeContent(chunks)
        self.content_length = content_length


def test_runtime_name_day_normalization_filters_current_calendar() -> None:
    """Only current namnlangd records are activated."""
    payload = {
        "data": [
            {
                "date": "2012-01-01T00:00:00",
                "namnlangd": "1",
                "title": f"Name {index}",
            }
            for index in range(500)
        ]
        + [
            {
                "date": "2012-01-01T00:00:00",
                "namnlangd": "0",
                "title": "Excluded",
            }
        ]
    }

    normalized = normalize_name_days(payload, "2026-07-19")

    assert "Excluded" not in normalized["days"][0]["names"]
    assert len(normalized["days"][0]["names"]) == 500


def test_runtime_theme_update_preserves_effective_dated_history() -> None:
    """A moved runtime theme day closes the old version and opens a new one."""
    existing = {
        "calendar_years": [2027],
        "days": [
            {
                "day": 4,
                "month": 10,
                "title": "Example",
                "url": "https://temadagar.se/example/",
                "year": 2027,
            }
        ],
    }
    current = {
        "calendar_years": [2028],
        "days": [
            {
                "day": 5,
                "month": 10,
                "title": "Example",
                "url": "https://temadagar.se/example/",
                "year": 2028,
            }
        ],
    }

    merged = merge_theme_history(existing, current, "2028-07-19")

    assert [item["valid_to"] for item in merged["days"]] == [
        "2028-07-19",
        None,
    ]


def test_dataset_fingerprint_ignores_retrieval_time() -> None:
    """Only normalized source content determines whether entities reload."""
    first = _dataset_metadata(
        source="https://example.test",
        retrieved_at="2026-07-19T10:00:00+00:00",
        records=[{"day": 1}],
        record_count=1,
    )
    second = _dataset_metadata(
        source="https://example.test",
        retrieved_at="2026-07-20T10:00:00+00:00",
        records=[{"day": 1}],
        record_count=1,
    )

    assert first["fingerprint"] == second["fingerprint"]
    assert first["retrieved_at"] != second["retrieved_at"]


async def test_response_reader_rejects_stream_larger_than_limit() -> None:
    """Chunked responses cannot bypass the configured download limit."""
    response = _FakeResponse((b"1234", b"5678"))

    with pytest.raises(SourceResponseTooLargeError):
        await _async_read_limited(response, 7)  # type: ignore[arg-type]


async def test_repeated_failures_create_repair_issue(hass) -> None:  # noqa: ANN001
    """Three consecutive failures preserve data and create one repair warning."""
    updater = SourceUpdater(hass, "entry")
    updater.data = {"last_successful_update": "2026-07-18T00:00:00+00:00"}
    updater.store.async_save = AsyncMock()

    with patch(
        "custom_components.swedish_calendar_plus.source_update.ir.async_create_issue"
    ) as create_issue:
        for _ in range(3):
            await updater._async_record_failure(ValueError("offline"))

    assert updater.data["last_successful_update"] == "2026-07-18T00:00:00+00:00"
    assert updater.data["consecutive_failures"] == 3
    create_issue.assert_called_once()
    assert create_issue.call_args.args[1:3] == (DOMAIN, SOURCE_UPDATE_ISSUE_ID)
