from flask import Blueprint, jsonify, request

from m3t.services.dynamic_values import DynamicValueService
from m3t.services.recipients import RecipientService
from m3t.services.templates import TemplateService


bp = Blueprint("api_templates", __name__)
template_service = TemplateService()
recipient_service = RecipientService()
dynamic_value_service = DynamicValueService()


@bp.get("/api/state")
def api_state():
    templates = template_service.list()
    recipient_set = recipient_service.list()
    dynamic_value_set = dynamic_value_service.list()
    template_lookup = {template.template_id: template for template in templates}
    recipient_errors = recipient_service.validate_all(recipient_set.rows, template_lookup)
    dynamic_errors = dynamic_value_service.validate_all(dynamic_value_set.rows)
    variables = sorted({column for column in recipient_set.columns} | {"from_name"})
    dynamic_variables = sorted(
        {
            row.get("dynamic_key", "").strip()
            for row in dynamic_value_set.rows
            if row.get("dynamic_key", "").strip()
        }
    )
    return jsonify(
        {
            "templates": [template.to_dict() for template in templates],
            "recipient_columns": recipient_set.columns,
            "recipients": recipient_set.rows,
            "recipient_errors": recipient_errors,
            "dynamic_values": dynamic_value_set.rows,
            "dynamic_errors": dynamic_errors,
            "variables": variables,
            "dynamic_variables": dynamic_variables,
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
