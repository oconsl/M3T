from __future__ import annotations

from m3t.domain import MailPreview, Template
from m3t.services.dynamic_values import DynamicValueService
from m3t.services.formatting import extract_dynamic_variables, extract_variables, normalize_message_format, render_template_text
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
        dynamic_options = DynamicValueService().enabled_options()
        dynamic_keys = set(extract_dynamic_variables(subject, body_text, body_html))
        missing_dynamic_values = sorted(key for key in dynamic_keys if not dynamic_options.get(key))
        dynamic_choices: dict[str, str] = {}
        rendered_html = render_template_text(body_html, values, dynamic_options, dynamic_choices) if message_format == "html" else ""
        return MailPreview(
            subject=render_template_text(subject, values, dynamic_options, dynamic_choices),
            body_text=render_template_text(body_text, values, dynamic_options, dynamic_choices),
            body_html=rendered_html,
            message_format=message_format,
            missing_variables=missing,
            missing_dynamic_values=missing_dynamic_values,
        )
