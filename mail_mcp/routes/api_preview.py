from flask import Blueprint, jsonify, request

from mail_mcp.services.preview import PreviewService
from mail_mcp.services.recipients import RecipientService
from mail_mcp.services.templates import TemplateService


bp = Blueprint("api_preview", __name__)
preview_service = PreviewService()
recipient_service = RecipientService()
template_service = TemplateService()


@bp.post("/api/preview")
def api_preview():
    payload = request.get_json(force=True)
    template_id = (payload.get("template_id") or "").strip()
    try:
        recipient_index = int(payload.get("recipient_index") or 0)
        preview = preview_service.render(
            template_id=template_id,
            recipient_index=recipient_index,
            payload=payload,
            templates=template_service.map(),
            recipients=recipient_service.list().rows,
        )
    except KeyError as exc:
        return jsonify({"ok": False, "errors": [str(exc).strip("'")]}), 404
    return jsonify({"ok": True, **preview.to_dict()})
