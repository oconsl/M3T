#!/usr/bin/env python3
import argparse
from pathlib import Path

from mail_mcp.config import ROOT
from mail_mcp.services.mailer import (
    GmailConfig,
    attach_files,
    authenticated_email,
    authorize,
    build_email,
    build_messages,
    encode_message,
    gmail_service,
    load_config,
    load_credentials,
    load_dotenv,
    load_messages,
    read_csv,
    read_template,
    send_messages,
    should_send,
    wants_html,
)
from mail_mcp.services.formatting import format_with_values as format_template


def main() -> None:
    parser = argparse.ArgumentParser(description="Envia emails desde recipients.csv usando Gmail API OAuth.")
    parser.add_argument("--recipients", default="recipients.csv", help="CSV con destinatarios.")
    parser.add_argument("--messages", default="messages.csv", help="CSV con templates y asuntos.")
    parser.add_argument("--auth", action="store_true", help="Conecta Gmail usando credentials.json y guarda token.json.")
    parser.add_argument("--send", action="store_true", help="Envia realmente. Sin esto solo hace dry-run.")
    args = parser.parse_args()

    service = None
    if args.auth:
        config = authorize()
        print(f"Gmail conectado: {config.user}")
        if not args.send:
            return
        service = gmail_service(interactive=False)
    else:
        service = gmail_service(interactive=False) if args.send else None
        config = load_config(authenticated_email()) if service else load_config()

    emails = build_messages(ROOT / Path(args.recipients), ROOT / Path(args.messages), config)

    if not args.send:
        print(f"Dry-run: {len(emails)} email(s) listos para enviar.")
        for email in emails:
            print(f"- {email['To']} | {email['Subject']}")
        print("Para conectar Gmail: .venv/bin/python send_emails.py --auth")
        print("Para enviar de verdad: .venv/bin/python send_emails.py --send")
        return

    send_messages(emails, service=service)
    print(f"Enviados: {len(emails)} email(s).")


if __name__ == "__main__":
    main()
