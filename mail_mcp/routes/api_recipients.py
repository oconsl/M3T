from flask import Blueprint, jsonify, request

from mail_mcp.services.recipients import RecipientService
from mail_mcp.services.templates import TemplateService


bp = Blueprint("api_recipients", __name__)
recipient_service = RecipientService()
template_service = TemplateService()


@bp.post("/api/recipients")
def api_save_recipients():
    payload = request.get_json(force=True)
    ok, errors, row_errors = recipient_service.save(
        columns=payload.get("columns") or [],
        incoming_rows=payload.get("rows") or [],
        templates=template_service.map(),
    )
    if not ok:
        return jsonify({"ok": False, "errors": errors, "recipient_errors": row_errors}), 400
    return jsonify({"ok": True})
