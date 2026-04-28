from dataclasses import dataclass, field


@dataclass(frozen=True)
class GmailConfig:
    user: str
    from_name: str
    reply_to: str


@dataclass
class Template:
    template_id: str
    subject: str
    body_text_file: str
    body_html_file: str
    body_text: str = ""
    body_html: str = ""
    variables: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "template_id": self.template_id,
            "subject": self.subject,
            "body_text_file": self.body_text_file,
            "body_html_file": self.body_html_file,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "variables": self.variables,
            "errors": self.errors,
        }


@dataclass
class RecipientSet:
    columns: list[str]
    rows: list[dict[str, str]]


@dataclass(frozen=True)
class DynamicValueSet:
    columns: list[str]
    rows: list[dict[str, str]]


@dataclass(frozen=True)
class MailPreview:
    subject: str
    body_text: str
    body_html: str
    message_format: str
    missing_variables: list[str]
    missing_dynamic_values: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "subject": self.subject,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "message_format": self.message_format,
            "missing_variables": self.missing_variables,
            "missing_dynamic_values": self.missing_dynamic_values,
        }
