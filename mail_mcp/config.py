from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MESSAGES_CSV = ROOT / "messages.csv"
RECIPIENTS_CSV = ROOT / "recipients.csv"
TEMPLATES_DIR = ROOT / "templates"
ATTACHMENTS_DIR = ROOT / "attachments"
BACKUPS_DIR = ROOT / "backups"
CREDENTIALS_FILE = ROOT / "credentials.json"
TOKEN_FILE = ROOT / "token.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

RECIPIENT_ID_COLUMN = "recipient_id"
STANDARD_RECIPIENT_COLUMNS = [
    "send",
    "email",
    "first_name",
    "last_name",
    "company",
    "template_id",
    "message_format",
    "attachment_paths",
    "custom_note",
]

TEMPLATE_COLUMNS = ["template_id", "subject", "body_text_file", "body_html_file"]
SEND_TRUE = {"yes", "si", "sí", "true", "1", "y"}
MESSAGE_FORMATS = {"plain", "html"}
HTML_FORMATS = {"html", "htm", "rich"}
