from flask import Blueprint, jsonify, request

from m3t.services.mailer import MailService, parse_selection


bp = Blueprint("api_mail", __name__)
mail_service = MailService()


@bp.post("/api/dry-run")
def api_dry_run():
    payload = request.get_json(silent=True) or {}
    indexes, recipient_ids = parse_selection(payload)
    return jsonify(mail_service.dry_run(indexes=indexes, recipient_ids=recipient_ids))


@bp.post("/api/send")
def api_send():
    payload = request.get_json(force=True)
    indexes, recipient_ids = parse_selection(payload)
    _, response, status = mail_service.send(
        confirm=payload.get("confirm"),
        indexes=indexes,
        recipient_ids=recipient_ids,
    )
    return jsonify(response), status
