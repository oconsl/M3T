from __future__ import annotations

from m3t.config import DYNAMIC_VALUE_COLUMNS, DYNAMIC_VALUES_CSV
from m3t.domain import DynamicValueSet
from m3t.repositories.csv_store import read_csv_rows, write_csv_rows


def list_dynamic_values() -> DynamicValueSet:
    columns, rows = read_csv_rows(DYNAMIC_VALUES_CSV)
    columns = columns or DYNAMIC_VALUE_COLUMNS
    return DynamicValueSet(columns=columns, rows=rows)


def save_dynamic_values(rows: list[dict[str, str]]) -> None:
    write_csv_rows(DYNAMIC_VALUES_CSV, DYNAMIC_VALUE_COLUMNS, rows)
