"""Download, validate, persist, and activate runtime source datasets."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from hashlib import sha256
from typing import TYPE_CHECKING, Final

from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .source_parsers import (
    NAME_DAY_URL,
    THEME_DAY_URL,
    NameDayPayload,
    SourceDatasetMetadata,
    SourceStorageData,
    merge_theme_history,
    normalize_name_days,
    normalize_theme_days,
)
from .sources import SourceRepository, load_theme_day_payload

if TYPE_CHECKING:
    from aiohttp import ClientResponse
    from homeassistant.core import HomeAssistant

STORAGE_VERSION: Final = 1
MAX_NAME_DAY_RESPONSE_BYTES: Final = 5 * 1024 * 1024
MAX_THEME_DAY_RESPONSE_BYTES: Final = 5 * 1024 * 1024
REPAIR_FAILURE_THRESHOLD: Final = 3
SOURCE_UPDATE_ISSUE_ID: Final = "source_update_failed"


class SourceResponseTooLargeError(ValueError):
    """Raised when a source response exceeds its safety limit."""


async def _async_read_limited(response: ClientResponse, limit: int) -> bytes:
    """Read an HTTP response without allowing unbounded memory use."""
    if response.content_length is not None and response.content_length > limit:
        msg = f"Source response exceeds {limit} bytes"
        raise SourceResponseTooLargeError(msg)
    result = bytearray()
    async for chunk in response.content.iter_chunked(64 * 1024):
        result.extend(chunk)
        if len(result) > limit:
            msg = f"Source response exceeds {limit} bytes"
            raise SourceResponseTooLargeError(msg)
    return bytes(result)


def _dataset_metadata(
    *,
    source: str,
    retrieved_at: str,
    records: object,
    record_count: int,
) -> SourceDatasetMetadata:
    """Return deterministic provenance metadata for normalized records."""
    canonical = json.dumps(
        records,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return {
        "source": source,
        "retrieved_at": retrieved_at,
        "record_count": record_count,
        "fingerprint": sha256(canonical).hexdigest(),
    }


def _normalize_name_source(source: bytes, retrieved_at: str) -> NameDayPayload:
    """Decode and normalize name-day JSON outside the event loop."""
    return normalize_name_days(json.loads(source), retrieved_at)


class SourceUpdater:
    """Manage last-known-good runtime source data."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize runtime source storage for a config entry."""
        self.hass = hass
        self.store: Store[SourceStorageData] = Store(
            hass, STORAGE_VERSION, f"swedish_calendar_plus.{entry_id}"
        )
        self.data: SourceStorageData = {}
        self.sources = SourceRepository()

    async def async_load(self) -> None:
        """Load and activate the last-known-good runtime datasets."""
        self.data = await self.store.async_load() or {}
        self.sources.activate(self.data.get("name_days"), self.data.get("theme_days"))
        if self.data.get("consecutive_failures", 0) >= REPAIR_FAILURE_THRESHOLD:
            self._create_repair_issue()

    async def async_refresh(self) -> bool:
        """Fetch and atomically activate both validated datasets."""
        try:
            changed = await self._async_refresh()
        except Exception as err:
            await self._async_record_failure(err)
            raise
        ir.async_delete_issue(self.hass, DOMAIN, SOURCE_UPDATE_ISSUE_ID)
        return changed

    async def _async_refresh(self) -> bool:
        """Perform a source refresh and return whether source content changed."""
        session = async_get_clientsession(self.hass)
        async with asyncio.timeout(30):
            async with session.get(NAME_DAY_URL) as response:
                response.raise_for_status()
                name_source = await _async_read_limited(
                    response, MAX_NAME_DAY_RESPONSE_BYTES
                )
            async with session.get(THEME_DAY_URL) as response:
                response.raise_for_status()
                theme_bytes = await _async_read_limited(
                    response, MAX_THEME_DAY_RESPONSE_BYTES
                )
                theme_source = theme_bytes.decode(response.charset or "utf-8")

        update_time = datetime.now(tz=UTC)
        retrieved_at = update_time.date().isoformat()
        name_days, theme_days = await asyncio.gather(
            self.hass.async_add_executor_job(
                _normalize_name_source, name_source, retrieved_at
            ),
            self.hass.async_add_executor_job(
                normalize_theme_days, theme_source, retrieved_at
            ),
        )
        name_metadata = _dataset_metadata(
            source=NAME_DAY_URL,
            retrieved_at=update_time.isoformat(),
            records=name_days["days"],
            record_count=sum(len(item["names"]) for item in name_days["days"]),
        )
        theme_metadata = _dataset_metadata(
            source=THEME_DAY_URL,
            retrieved_at=update_time.isoformat(),
            records=theme_days["days"],
            record_count=len(theme_days["days"]),
        )
        changed = (
            self.data.get("name_days_metadata", {}).get("fingerprint")
            != name_metadata["fingerprint"]
            or self.data.get("theme_days_metadata", {}).get("fingerprint")
            != theme_metadata["fingerprint"]
        )
        if changed:
            theme_days = merge_theme_history(
                self.data.get("theme_days") or load_theme_day_payload(),
                theme_days,
                retrieved_at,
            )
            active_name_days = name_days
            active_theme_days = theme_days
        else:
            active_name_days = self.data["name_days"]
            active_theme_days = self.data["theme_days"]
        candidate: SourceStorageData = {
            "last_successful_update": update_time.isoformat(),
            "consecutive_failures": 0,
            "name_days_metadata": name_metadata,
            "theme_days_metadata": theme_metadata,
            "name_days": active_name_days,
            "theme_days": active_theme_days,
        }
        await self.store.async_save(candidate)
        self.data = candidate
        self.sources.activate(active_name_days, active_theme_days)
        return changed

    async def _async_record_failure(self, err: Exception) -> None:
        """Persist failure state and create a repair after repeated failures."""
        failure_count = self.data.get("consecutive_failures", 0) + 1
        self.data = {
            **self.data,
            "consecutive_failures": failure_count,
            "last_update_error": str(err),
        }
        await self.store.async_save(self.data)
        if failure_count >= REPAIR_FAILURE_THRESHOLD:
            self._create_repair_issue()

    def _create_repair_issue(self) -> None:
        """Create the persistent source-update repair warning."""
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            SOURCE_UPDATE_ISSUE_ID,
            is_fixable=False,
            is_persistent=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key="source_update_failed",
        )
