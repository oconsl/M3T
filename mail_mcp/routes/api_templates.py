from flask import Blueprint, jsonify, request

from mail_mcp.services.recipients import RecipientService
from mail_mcp.services.templates import TemplateService


bp = Blueprint("api_templates", __name__)
template_service = TemplateService()
recipient_service = RecipientService()


@bp.get("/api/state")
def api_state():
    templates = template_service.list()
    recipient_set = recipient_service.list()
    template_lookup = {template.template_id: template for template in templates}
    recipient_errors = recipient_service.validate_all(recipient_set.rows, template_lookup)
    variables = sorted({column for column in recipient_set.columns} | {"from_name"})
    return jsonify(
        {
            "templates": [template.to_dict() for template in templates],
            "recipient_columns": recipient_set.columns,
            "recipients": recipient_set.rows,
            "recipient_errors": recipient_errors,
            "variables": variables,
        }
    )


@bp.post("/api/templates")
def api_save_template():
    payload = request.get_json(force=True)
    errors = template_service.save(payload)
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400
    return jsonify({"ok": True})


@bp.post("/api/templates/duplicate")
def api_duplicate_template():
    payload = request.get_json(force=True)
    ok, errors = template_service.duplicate(
        source_id=(payload.get("source_id") or "").strip(),
        new_id=(payload.get("new_id") or "").strip(),
    )
    if not ok:
        status = 404 if errors == ["Template origen no existe."] else 400
        return jsonify({"ok": False, "errors": errors}), status
    return jsonify({"ok": True})


@bp.delete("/api/templates/<template_id>")
def api_delete_template(template_id: str):
    recipients = recipient_service.list().rows
    ok, errors, status = template_service.delete(template_id, recipients)
    if not ok:
        return jsonify({"ok": False, "errors": errors}), status
    return jsonify({"ok": True})
