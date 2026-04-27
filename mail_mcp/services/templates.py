from __future__ import annotations

from mail_mcp.config import TEMPLATE_COLUMNS
from mail_mcp.domain import Template
from mail_mcp.repositories.csv_store import make_backup
from mail_mcp.repositories.template_store import (
    default_template_paths,
    delete_template_files,
    list_templates,
    safe_template_path,
    template_map,
    write_template_index,
)
from mail_mcp.services.formatting import TEMPLATE_ID_RE


class TemplateService:
    def list(self) -> list[Template]:
        return list_templates()

    def map(self) -> dict[str, Template]:
        return template_map()

    def validate_payload(self, payload: dict, existing_ids: set[str], original_id: str = "") -> list[str]:
        errors = []
        template_id = (payload.get("template_id") or "").strip()
        subject = (payload.get("subject") or "").strip()
        body_text = payload.get("body_text") or ""
        body_html = payload.get("body_html") or ""

        if not template_id:
            errors.append("template_id es requerido.")
        elif not TEMPLATE_ID_RE.match(template_id):
            errors.append("template_id solo puede usar letras, numeros, guiones y guiones bajos.")
        elif template_id != original_id and template_id in existing_ids:
            errors.append("template_id ya existe.")
        if not subject:
            errors.append("subject es requerido.")
        if not body_text.strip():
            errors.append("El cuerpo TXT es requerido.")
        if body_html.strip():
            _, html_path = default_template_paths(template_id)
            try:
                safe_template_path(html_path, ".html")
            except ValueError as exc:
                errors.append(str(exc))
        return errors

    def save(self, payload: dict) -> list[str]:
        original_id = (payload.get("original_id") or "").strip()
        templates = self.list()
        errors = self.validate_payload(payload, {template.template_id for template in templates}, original_id)
        if errors:
            return errors

        template_id = payload["template_id"].strip()
        subject = payload["subject"].strip()
        body_text = payload.get("body_text") or ""
        body_html = payload.get("body_html") or ""
        body_text_file, body_html_file = default_template_paths(template_id)
        make_backup()

        text_path = safe_template_path(body_text_file, ".txt")
        html_path = safe_template_path(body_html_file, ".html")
        text_path.write_text(body_text, encoding="utf-8")
        if body_html.strip():
            html_path.write_text(body_html, encoding="utf-8")
        elif html_path.exists():
            html_path.unlink()
            body_html_file = ""
        else:
            body_html_file = ""

        rows = []
        replaced = False
        for template in templates:
            if template.template_id == original_id:
                rows.append(
                    {
                        "template_id": template_id,
                        "subject": subject,
                        "body_text_file": body_text_file,
                        "body_html_file": body_html_file,
                    }
                )
                replaced = True
                if original_id != template_id:
                    delete_template_files(template)
            else:
                rows.append(_template_index_row(template))
        if not replaced:
            rows.append(
                {
                    "template_id": template_id,
                    "subject": subject,
                    "body_text_file": body_text_file,
                    "body_html_file": body_html_file,
                }
            )

        write_template_index(rows)
        return []

    def duplicate(self, source_id: str, new_id: str) -> tuple[bool, list[str]]:
        templates = self.map()
        if source_id not in templates:
            return False, ["Template origen no existe."]
        source = templates[source_id]
        draft = {
            "template_id": new_id,
            "subject": source.subject,
            "body_text": source.body_text,
            "body_html": source.body_html,
        }
        errors = self.validate_payload(draft, set(templates), "")
        if errors:
            return False, errors

        body_text_file, body_html_file = default_template_paths(new_id)
        make_backup()
        safe_template_path(body_text_file, ".txt").write_text(source.body_text, encoding="utf-8")
        if source.body_html.strip():
            safe_template_path(body_html_file, ".html").write_text(source.body_html, encoding="utf-8")
        else:
            body_html_file = ""

        rows = [_template_index_row(template) for template in templates.values()]
        rows.append(
            {
                "template_id": new_id,
                "subject": source.subject,
                "body_text_file": body_text_file,
                "body_html_file": body_html_file,
            }
        )
        write_template_index(rows)
        return True, []

    def delete(self, template_id: str, recipients: list[dict[str, str]]) -> tuple[bool, list[str], int]:
        templates = self.list()
        if any(row.get("template_id") == template_id for row in recipients):
            return False, ["Hay recipients usando este template. Cambialos antes de borrar."], 400

        kept = [template for template in templates if template.template_id != template_id]
        deleted = [template for template in templates if template.template_id == template_id]
        if not deleted:
            return False, ["Template no encontrado."], 404

        make_backup()
        for template in deleted:
            delete_template_files(template)
        write_template_index([_template_index_row(template) for template in kept])
        return True, [], 200


def _template_index_row(template: Template) -> dict[str, str]:
    return {column: getattr(template, column) for column in TEMPLATE_COLUMNS}
