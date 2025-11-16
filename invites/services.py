import csv
import io
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Set

import requests
from django.conf import settings
from django.utils import timezone

from .models import Invitee

logger = logging.getLogger(__name__)


class SheetSyncError(Exception):
    """Raised when the Google Sheet cannot be retrieved."""


@dataclass
class SheetSyncResult:
    matched_count: int = 0
    updated_count: int = 0
    source_count: int = 0
    synced_at: Optional[datetime] = None


_LAST_SYNC_RESULT: Optional[SheetSyncResult] = None
_LAST_SYNCED_AT: Optional[datetime] = None


def _normalize(text: str) -> str:
    return "".join(text.split()).casefold()


def _fetch_sheet_names() -> Set[str]:
    sheet_id = getattr(settings, "GOOGLE_SHEET_ID", "")
    gid = getattr(settings, "GOOGLE_SHEET_GID", "")
    if not sheet_id or not gid:
        raise SheetSyncError("缺少 Google Sheet 設定")

    csv_url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export"
        f"?format=csv&gid={gid}"
    )

    try:
        response = requests.get(csv_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("同步 Google Sheet 失敗：%s", exc)
        raise SheetSyncError("無法連線到 Google Sheet") from exc

    decoded = response.content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(decoded))
    names: Set[str] = set()
    for index, row in enumerate(reader):
        if index == 0:
            continue
        if not row:
            continue
        column_value = ""
        if len(row) > 1:
            column_value = row[1].strip()
        if not column_value and row:
            column_value = row[0].strip()
        if column_value:
            names.add(_normalize(column_value))
    return names


def sync_invitees_with_sheet(cache_seconds: int = 120) -> SheetSyncResult:
    """
    Pull the Google Sheet once in ``cache_seconds`` and sync invitees.
    Returns a SheetSyncResult describing the sync.
    """
    global _LAST_SYNCED_AT, _LAST_SYNC_RESULT

    now = timezone.now()
    if (
        _LAST_SYNCED_AT
        and (now - _LAST_SYNCED_AT).total_seconds() < cache_seconds
        and _LAST_SYNC_RESULT
    ):
        return _LAST_SYNC_RESULT

    names = _fetch_sheet_names()
    matched_count = 0
    to_update: list[Invitee] = []
    invitees = Invitee.objects.all()

    for invitee in invitees:
        is_present = _normalize(invitee.name) in names
        if is_present:
            matched_count += 1
        changed = False
        if invitee.sheet_confirmed != is_present:
            invitee.sheet_confirmed = is_present
            changed = True

        if is_present:
            if invitee.status not in (
                Invitee.Status.ACCEPTED,
                Invitee.Status.DECLINED,
            ):
                invitee.status = Invitee.Status.ACCEPTED
                changed = True
        else:
            if invitee.status in (
                Invitee.Status.ACCEPTED,
                Invitee.Status.INVITED,
            ):
                invitee.status = Invitee.Status.PENDING
                changed = True

        if changed:
            to_update.append(invitee)

    if to_update:
        Invitee.objects.bulk_update(to_update, ["sheet_confirmed", "status"])

    result = SheetSyncResult(
        matched_count=matched_count,
        updated_count=len(to_update),
        source_count=len(names),
        synced_at=now,
    )
    _LAST_SYNCED_AT = now
    _LAST_SYNC_RESULT = result
    return result
