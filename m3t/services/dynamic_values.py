from __future__ import annotations

from m3t.domain import DynamicValueSet
from m3t.repositories.csv_store import make_backup
from m3t.repositories.dynamic_value_store import list_dynamic_values, save_dynamic_values
from m3t.services.formatting import DYNAMIC_KEY_RE, normalize_send


class DynamicValueService:
    def list(self) -> DynamicValueSet:
        return list_dynamic_values()

    def normalize_rows(self, incoming_rows: list[dict[str, str]]) -> list[dict[str, str]]:
        rows = []
        for row in incoming_rows:
            rows.append(
                {
                    "dynamic_key": str(row.get("dynamic_key", "") or "").strip(),
                    "value": str(row.get("value", "") or ""),
                    "enabled": normalize_send(str(row.get("enabled", "") or "")),
                }
            )
        return rows

    def save(self, incoming_rows: list[dict[str, str]]) -> tuple[bool, list[str], list[list[str]]]:
        rows = self.normalize_rows(incoming_rows)
        row_errors = self.validate_all(rows)
        errors = [error for row in row_errors for error in row]
        if errors:
            return False, errors, row_errors

        make_backup()
        save_dynamic_values(rows)
        return True, [], []

    def validate_all(self, rows: list[dict[str, str]]) -> list[list[str]]:
        return [self.validate(row, index) for index, row in enumerate(rows)]

    def validate(self, row: dict[str, str], index: int) -> list[str]:
        errors = []
        dynamic_key = row.get("dynamic_key", "")
        if not dynamic_key:
            errors.append("dynamic_key requerido.")
        elif not DYNAMIC_KEY_RE.match(dynamic_key):
            errors.append("dynamic_key solo puede usar letras, numeros y guiones bajos; no puede empezar con numero.")
        if not (row.get("value") or "").strip():
            errors.append("value requerido.")
        return [f"Fila {index + 1}: {error}" for error in errors]

    def enabled_options(self) -> dict[str, list[str]]:
        options: dict[str, list[str]] = {}
        for row in self.list().rows:
            key = (row.get("dynamic_key") or "").strip()
            value = row.get("value") or ""
            if not key or not value.strip() or normalize_send(row.get("enabled", "")) != "yes":
                continue
            options.setdefault(key, []).append(value)
        return options
