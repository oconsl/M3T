from __future__ import annotations

from pathlib import Path

from m3t.config import MESSAGES_CSV, TEMPLATE_COLUMNS, TEMPLATES_DIR
from m3t.domain import Template
from m3t.repositories.csv_store import read_csv_rows, write_csv_rows
from m3t.services.formatting import extract_variables


def safe_template_path(relative_path: str, suffix: str | None = None) -> Path:
    if not relative_path:
        raise ValueError("La ruta del template es requerida.")
    path = (TEMPLATES_DIR.parent / relative_path).resolve()
    templates_root = TEMPLATES_DIR.resolve()
    try:
        path.relative_to(templates_root)
    except ValueError as exc:
        raise ValueError("La ruta debe estar dentro de templates/.") from exc
    if suffix and path.suffix != suffix:
        raise ValueError(f"La ruta debe terminar en {suffix}.")
    return path


def default_template_paths(template_id: str) -> tuple[str, str]:
    return f"templates/{template_id}.txt", f"templates/{template_id}.html"


def list_templates() -> list[Template]:
    _, rows = read_csv_rows(MESSAGES_CSV)
    templates = []
    for row in rows:
        template_id = row.get("template_id", "").strip()
        subject = row.get("subject", "")
        body_text_file = row.get("body_text_file", "")
        body_html_file = row.get("body_html_file", "")
        text_body = ""
        html_body = ""
        errors = []

        try:
            text_body = safe_template_path(body_text_file, ".txt").read_text(encoding="utf-8")
        except Exception as exc:
            errors.append(str(exc))
        if body_html_file.strip():
            try:
                html_body = safe_template_path(body_html_file, ".html").read_text(encoding="utf-8")
            except Exception as exc:
                errors.append(str(exc))

        templates.append(
            Template(
                template_id=template_id,
                subject=subject,
                body_text_file=body_text_file,
                body_html_file=body_html_file,
                body_text=text_body,
                body_html=html_body,
                variables=extract_variables(subject, text_body, html_body),
                errors=errors,
            )
        )
    return templates


def template_map() -> dict[str, Template]:
    return {template.template_id: template for template in list_templates()}


def write_template_index(rows: list[dict[str, str]]) -> None:
    write_csv_rows(MESSAGES_CSV, TEMPLATE_COLUMNS, rows)


def delete_template_files(template: Template) -> None:
    for relative, suffix in (
        (template.body_text_file, ".txt"),
        (template.body_html_file, ".html"),
    ):
        if not relative:
            continue
        try:
            path = safe_template_path(relative, suffix)
        except ValueError:
            continue
        if path.exists():
            path.unlink()
