from __future__ import annotations

import hashlib
import uuid

from m3t.config import RECIPIENT_ID_COLUMN, RECIPIENTS_CSV, STANDARD_RECIPIENT_COLUMNS
from m3t.domain import RecipientSet
from m3t.repositories.csv_store import merge_columns, read_csv_rows, write_csv_rows
from m3t.services.formatting import normalize_message_format, normalize_send


def _fallback_recipient_id(row: dict[str, str], index: int) -> str:
    identity = "|".join(f"{key}={row.get(key, '')}" for key in sorted(row) if key != RECIPIENT_ID_COLUMN)
    digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:12]
    return f"row-{index + 1}-{digest}"


def list_recipients() -> RecipientSet:
    discovered_columns, rows = read_csv_rows(RECIPIENTS_CSV)
    storage_columns = merge_columns([RECIPIENT_ID_COLUMN, *STANDARD_RECIPIENT_COLUMNS], discovered_columns)
    visible_columns = [column for column in storage_columns if column != RECIPIENT_ID_COLUMN]
    normalized_rows = []
    for index, row in enumerate(rows):
        normalized = {column: row.get(column, "") for column in storage_columns}
        normalized[RECIPIENT_ID_COLUMN] = normalized.get(RECIPIENT_ID_COLUMN) or _fallback_recipient_id(row, index)
        normalized["message_format"] = normalize_message_format(normalized.get("message_format", ""))
        normalized_rows.append(normalized)
    return RecipientSet(columns=visible_columns, rows=normalized_rows)


def save_recipients(columns: list[str], rows: list[dict[str, str]]) -> None:
    visible_columns = [column for column in columns if column and column != RECIPIENT_ID_COLUMN]
    storage_columns = merge_columns([RECIPIENT_ID_COLUMN, *STANDARD_RECIPIENT_COLUMNS], visible_columns)
    clean_rows = []
    for row in rows:
        clean = {column: str(row.get(column, "") or "") for column in storage_columns}
        clean[RECIPIENT_ID_COLUMN] = clean.get(RECIPIENT_ID_COLUMN) or uuid.uuid4().hex
        clean["send"] = normalize_send(clean.get("send", ""))
        clean["message_format"] = normalize_message_format(clean.get("message_format", ""))
        clean_rows.append(clean)
    write_csv_rows(RECIPIENTS_CSV, storage_columns, clean_rows)
