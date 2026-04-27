from __future__ import annotations

import base64
import csv
import mimetypes
import os
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from mail_mcp.config import CREDENTIALS_FILE, HTML_FORMATS, RECIPIENTS_CSV, ROOT, SCOPES, TOKEN_FILE
from mail_mcp.domain import GmailConfig
from mail_mcp.repositories.recipient_store import list_recipients
from mail_mcp.repositories.template_store import safe_template_path
from mail_mcp.services.formatting import SafeDict, format_with_values, should_send
from mail_mcp.services.recipients import safe_attachment_path


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def load_messages(path: Path) -> dict[str, dict[str, str]]:
    rows = read_csv(path)
    messages = {}
    for row in rows:
        template_id = row.get("template_id", "").strip()
        if not template_id:
            continue
        messages[template_id] = row
    return messages


def wants_html(row: dict[str, str]) -> bool:
    return (row.get("message_format") or "html").strip().lower() in HTML_FORMATS


def read_template(relative_path: str) -> str:
    path = safe_template_path(relative_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el template: {relative_path}")
    return path.read_text(encoding="utf-8")


def attach_files(message: EmailMessage, attachment_paths: str) -> None:
    if not attachment_paths.strip():
        return

    for raw_path in attachment_paths.split(";"):
        raw_path = raw_path.strip()
        if not raw_path:
            continue

        path = safe_attachment_path(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"No existe el adjunto: {raw_path}")

        content_type, _ = mimetypes.guess_type(path)
        maintype, subtype = (content_type or "application/octet-stream").split("/", 1)
        message.add_attachment(
            path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=path.name,
        )


def build_email(
    recipient: dict[str, str],
    template: dict[str, str],
    config: GmailConfig,
) -> EmailMessage:
    values = SafeDict({**recipient, **template, "from_name": config.from_name})
    subject = format_with_values(template["subject"], values)
    text = format_with_values(read_template(template["body_text_file"]), values)
    html_file = template.get("body_html_file", "").strip()
    html = format_with_values(read_template(html_file), values) if html_file else ""

    message = EmailMessage()
    message["From"] = f"{config.from_name} <{config.user}>"
    message["To"] = recipient["email"].strip()
    message["Subject"] = subject
    if config.reply_to:
        message["Reply-To"] = config.reply_to

    message.set_content(text)
    if html and wants_html(recipient):
        message.add_alternative(html, subtype="html")

    attach_files(message, recipient.get("attachment_paths", ""))
    return message


def load_config(user_email: str = "") -> GmailConfig:
    load_dotenv(ROOT / ".env")

    sender = user_email or os.environ.get("GMAIL_USER", "")
    if not sender:
        sender = "me"

    return GmailConfig(
        user=sender,
        from_name=os.environ.get("FROM_NAME", sender),
        reply_to=os.environ.get("REPLY_TO", ""),
    )


def preview_config() -> GmailConfig:
    load_dotenv(ROOT / ".env")
    return GmailConfig(
        user=os.environ.get("GMAIL_USER", "preview@example.com"),
        from_name=os.environ.get("FROM_NAME", "Preview"),
        reply_to=os.environ.get("REPLY_TO", ""),
    )


def load_credentials(interactive: bool = False) -> Credentials:
    if not CREDENTIALS_FILE.exists():
        raise RuntimeError("No existe credentials.json en la raiz del proyecto.")

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not interactive:
            raise RuntimeError(
                "Gmail no esta conectado. Ejecuta: .venv/bin/python send_emails.py --auth"
            )
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds


def gmail_service(interactive: bool = False):
    creds = load_credentials(interactive=interactive)
    return build("gmail", "v1", credentials=creds)


def authenticated_email() -> str:
    load_dotenv(ROOT / ".env")
    return os.environ.get("GMAIL_USER", "me")


def encode_message(message: EmailMessage) -> dict[str, str]:
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"raw": raw}


def send_messages(messages: list[EmailMessage], service=None) -> list[dict]:
    service = service or gmail_service(interactive=False)
    sent = []
    for message in messages:
        result = service.users().messages().send(userId="me", body=encode_message(message)).execute()
        sent.append(result)
    return sent


def authorize() -> GmailConfig:
    gmail_service(interactive=True)
    return load_config(authenticated_email())


def build_messages(recipients_path: Path, messages_path: Path, config: GmailConfig) -> list[EmailMessage]:
    templates = load_messages(messages_path)
    recipients = [row for row in read_csv(recipients_path) if should_send(row)]
    emails = []
    for recipient in recipients:
        template_id = recipient.get("template_id", "").strip()
        if template_id not in templates:
            raise RuntimeError(f"Template no encontrado para {recipient.get('email')}: {template_id}")
        emails.append(build_email(recipient, templates[template_id], config))
    return emails


class MailService:
    def selected_recipients(
        self,
        indexes: list[int] | None = None,
        recipient_ids: list[str] | None = None,
    ) -> list[dict[str, str]]:
        rows = list_recipients().rows
        if recipient_ids is not None:
            wanted = set(recipient_ids)
            return [row for row in rows if row.get("recipient_id") in wanted]
        if indexes is None:
            return [row for row in rows if should_send(row)]
        return [rows[index] for index in indexes if 0 <= index < len(rows)]

    def dry_run(
        self,
        indexes: list[int] | None = None,
        recipient_ids: list[str] | None = None,
        messages_path: Path | None = None,
    ) -> dict[str, object]:
        templates = load_messages(messages_path or (ROOT / "messages.csv"))
        config = preview_config()
        emails = []
        errors = []
        for recipient in self.selected_recipients(indexes=indexes, recipient_ids=recipient_ids):
            template_id = recipient.get("template_id", "").strip()
            if template_id not in templates:
                errors.append(f"Template no encontrado para {recipient.get('email')}: {template_id}")
                continue
            try:
                email = build_email(recipient, templates[template_id], config)
                emails.append(
                    {
                        "to": email["To"],
                        "subject": email["Subject"],
                        "message_format": recipient.get("message_format", "html") or "html",
                    }
                )
            except Exception as exc:
                errors.append(str(exc))
        return {"ok": not errors, "emails": emails, "errors": errors}

    def send(
        self,
        confirm: str,
        indexes: list[int] | None = None,
        recipient_ids: list[str] | None = None,
    ) -> tuple[bool, dict[str, object], int]:
        if confirm != "SEND":
            return False, {"ok": False, "errors": ["Confirmacion requerida."]}, 400
        service = gmail_service(interactive=False)
        config = load_config(authenticated_email())
        templates = load_messages(ROOT / "messages.csv")
        emails = []
        for recipient in self.selected_recipients(indexes=indexes, recipient_ids=recipient_ids):
            template_id = recipient.get("template_id", "").strip()
            if template_id not in templates:
                return False, {"ok": False, "errors": [f"Template no encontrado: {template_id}"]}, 400
            emails.append(build_email(recipient, templates[template_id], config))
        send_messages(emails, service=service)
        return True, {"ok": True, "sent": len(emails)}, 200


def parse_selection(payload: dict) -> tuple[list[int] | None, list[str] | None]:
    indexes = payload.get("indexes")
    recipient_ids = payload.get("recipient_ids")
    if recipient_ids is not None:
        recipient_ids = [str(recipient_id) for recipient_id in recipient_ids]
    if indexes is not None:
        indexes = [int(index) for index in indexes]
    return indexes, recipient_ids
