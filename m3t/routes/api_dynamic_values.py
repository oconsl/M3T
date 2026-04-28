from flask import Blueprint, jsonify, request

from m3t.services.dynamic_values import DynamicValueService


bp = Blueprint("api_dynamic_values", __name__)
dynamic_value_service = DynamicValueService()


@bp.post("/api/dynamic-values")
def api_save_dynamic_values():
    payload = request.get_json(force=True)
    ok, errors, row_errors = dynamic_value_service.save(payload.get("rows") or [])
    if not ok:
        return jsonify({"ok": False, "errors": errors, "dynamic_errors": row_errors}), 400
    return jsonify({"ok": True})
