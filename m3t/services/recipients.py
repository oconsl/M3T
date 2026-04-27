from __future__ import annotations

from m3t.config import ATTACHMENTS_DIR
from m3t.domain import RecipientSet, Template
from m3t.repositories.csv_store import make_backup, merge_columns
from m3t.repositories.recipient_store import list_recipients, save_recipients
from m3t.services.formatting import EMAIL_RE, normalize_message_format, normalize_send


class RecipientService:
    def list(self) -> RecipientSet:
        return list_recipients()

    def normalize_rows(self, columns: list[str], incoming_rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
        current = self.list()
        normalized_columns = merge_columns(current.columns, [column for column in columns if column])
        rows = []
        for row in incoming_rows:
            clean = {column: str(row.get(column, "") or "") for column in normalized_columns}
            if row.get("recipient_id"):
                clean["recipient_id"] = str(row.get("recipient_id"))
            clean["send"] = normalize_send(clean.get("send", ""))
            clean["message_format"] = normalize_message_format(clean.get("message_format", ""))
            rows.append(clean)
        return normalized_columns, rows

    def save(self, columns: list[str], incoming_rows: list[dict[str, str]], templates: dict[str, Template]) -> tuple[bool, list[str], list[list[str]]]:
        columns, rows = self.normalize_rows(columns, incoming_rows)
        row_errors = self.validate_all(rows, templates)
        errors = [error for row in row_errors for error in row]
        if errors:
            return False, errors, row_errors

        make_backup()
        save_recipients(columns, rows)
        return True, [], []

    def validate_all(self, rows: list[dict[str, str]], templates: dict[str, Template]) -> list[list[str]]:
        return [self.validate(row, templates, index) for index, row in enumerate(rows)]

    def validate(self, row: dict[str, str], templates: dict[str, Template], index: int) -> list[str]:
        errors = []
        email = (row.get("email") or "").strip()
        template_id = (row.get("template_id") or "").strip()
        message_format = normalize_message_format(row.get("message_format", ""))
        if not email:
            errors.append("email requerido.")
        elif not EMAIL_RE.match(email):
            errors.append("email invalido.")
        if not template_id:
            errors.append("template_id requerido.")
        elif template_id not in templates:
            errors.append("template_id no existe.")
        elif message_format == "html" and not templates[template_id].body_html_file.strip():
            errors.append("message_format html requiere un template HTML.")

        for raw_path in (row.get("attachment_paths") or "").split(";"):
            raw_path = raw_path.strip()
            if not raw_path:
                continue
            try:
                path = safe_attachment_path(raw_path)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if not path.exists():
                errors.append(f"adjunto inexistente: {raw_path}")
        return [f"Fila {index + 1}: {error}" for error in errors]


def safe_attachment_path(relative_path: str):
    path = (ATTACHMENTS_DIR.parent / relative_path).resolve()
    attachments_root = ATTACHMENTS_DIR.resolve()
    try:
        path.relative_to(attachments_root)
    except ValueError as exc:
        raise ValueError(f"adjunto fuera de attachments/: {relative_path}") from exc
    return path
