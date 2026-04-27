from __future__ import annotations

from m3t.domain import MailPreview, Template
from m3t.services.formatting import extract_variables, format_with_values, normalize_message_format
from m3t.services.mailer import preview_config


class PreviewService:
    def render(
        self,
        template_id: str,
        recipient_index: int,
        payload: dict,
        templates: dict[str, Template],
        recipients: list[dict[str, str]],
    ) -> MailPreview:
        if template_id not in templates:
            raise KeyError("Template no encontrado.")
        if not recipients:
            values = {"from_name": preview_config().from_name}
        else:
            recipient_index = max(0, min(recipient_index, len(recipients) - 1))
            values = {**recipients[recipient_index], "from_name": preview_config().from_name}

        template = templates[template_id]
        subject = payload.get("subject", template.subject)
        body_text = payload.get("body_text", template.body_text)
        body_html = payload.get("body_html", template.body_html)
        message_format = normalize_message_format(payload.get("message_format") or values.get("message_format", ""))
        all_variables = set(extract_variables(subject, body_text, body_html))
        missing = sorted(variable for variable in all_variables if not values.get(variable))
        rendered_html = format_with_values(body_html, values) if message_format == "html" else ""
        return MailPreview(
            subject=format_with_values(subject, values),
            body_text=format_with_values(body_text, values),
            body_html=rendered_html,
            message_format=message_format,
            missing_variables=missing,
        )
