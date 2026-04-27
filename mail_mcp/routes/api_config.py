from flask import Blueprint, jsonify

from mail_mcp.config import CREDENTIALS_FILE, TOKEN_FILE
from mail_mcp.services.mailer import authenticated_email, authorize, gmail_service


bp = Blueprint("api_config", __name__)


@bp.get("/api/config")
def api_config():
    try:
        connected = TOKEN_FILE.exists()
        email = ""
        if connected:
            gmail_service(interactive=False)
            email = authenticated_email()
        return jsonify(
            {
                "ok": True,
                "connected": connected,
                "email": email,
                "credentials_file": CREDENTIALS_FILE.exists(),
            }
        )
    except Exception as exc:
        return jsonify(
            {
                "ok": False,
                "connected": False,
                "credentials_file": CREDENTIALS_FILE.exists(),
                "errors": [str(exc)],
            }
        )


@bp.post("/api/auth")
def api_auth():
    try:
        config = authorize()
        return jsonify({"ok": True, "email": config.user})
    except Exception as exc:
        return jsonify({"ok": False, "errors": [str(exc)]}), 400
