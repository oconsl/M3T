import unittest
from email.message import EmailMessage
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from m3t import create_app
from m3t.services.dynamic_values import DynamicValueService
from m3t.services.mailer import send_messages
from m3t.services.formatting import extract_variables, normalize_message_format, normalize_send, render_template_text
from m3t.services.recipients import safe_attachment_path


class FakeGmailService:
    def __init__(self):
        self.sent_bodies = []

    def users(self):
        return self

    def messages(self):
        return self

    def send(self, userId, body):
        self.sent_bodies.append((userId, body))
        return self

    def execute(self):
        return {"id": f"message-{len(self.sent_bodies)}"}


class ServiceTests(unittest.TestCase):
    def test_formatting_helpers(self):
        self.assertEqual(normalize_send("sí"), "yes")
        self.assertEqual(normalize_send("no"), "no")
        self.assertEqual(normalize_message_format("plain"), "plain")
        self.assertEqual(normalize_message_format("bad"), "html")
        self.assertEqual(
            extract_variables("{dynamic.saludo} {first_name}", "{{ignored}}", "{company}"),
            ["company", "first_name"],
        )

    def test_dynamic_values_render_before_recipient_values(self):
        rendered = render_template_text(
            "{dynamic.saludo} {first_name}",
            {"first_name": "Ana"},
            {"saludo": ["Hola"]},
        )

        self.assertEqual(rendered, "Hola Ana")

    def test_dynamic_values_keep_unknown_placeholders(self):
        rendered = render_template_text(
            "{dynamic.inexistente} {first_name}",
            {"first_name": "Ana"},
            {},
        )

        self.assertEqual(rendered, "{dynamic.inexistente} Ana")

    def test_dynamic_values_reuse_choice_within_render(self):
        choices = {"saludo": ["Hola", "Saludos"]}
        rendered = render_template_text(
            "{dynamic.saludo} y {dynamic.saludo}",
            {},
            choices,
            chooser=lambda options: options[1],
        )

        self.assertEqual(rendered, "Saludos y Saludos")

    def test_dynamic_service_ignores_disabled_options(self):
        with TemporaryDirectory() as temp_dir:
            dynamic_csv = Path(temp_dir) / "dynamic_values.csv"
            backup_dir = Path(temp_dir) / "backups"
            with patch("m3t.repositories.dynamic_value_store.DYNAMIC_VALUES_CSV", dynamic_csv), \
                patch("m3t.repositories.csv_store.DYNAMIC_VALUES_CSV", dynamic_csv), \
                patch("m3t.repositories.csv_store.MESSAGES_CSV", Path(temp_dir) / "messages.csv"), \
                patch("m3t.repositories.csv_store.RECIPIENTS_CSV", Path(temp_dir) / "recipients.csv"), \
                patch("m3t.repositories.csv_store.TEMPLATES_DIR", Path(temp_dir) / "templates"), \
                patch("m3t.repositories.csv_store.BACKUPS_DIR", backup_dir):
                service = DynamicValueService()
                ok, errors, _ = service.save(
                    [
                        {"dynamic_key": "saludo", "value": "Hola", "enabled": "yes"},
                        {"dynamic_key": "saludo", "value": "No usar", "enabled": "no"},
                    ]
                )

                self.assertTrue(ok)
                self.assertEqual(errors, [])
                self.assertEqual(service.enabled_options(), {"saludo": ["Hola"]})

    def test_dynamic_values_api_saves_rows(self):
        with TemporaryDirectory() as temp_dir:
            dynamic_csv = Path(temp_dir) / "dynamic_values.csv"
            backup_dir = Path(temp_dir) / "backups"
            with patch("m3t.repositories.dynamic_value_store.DYNAMIC_VALUES_CSV", dynamic_csv), \
                patch("m3t.repositories.csv_store.DYNAMIC_VALUES_CSV", dynamic_csv), \
                patch("m3t.repositories.csv_store.MESSAGES_CSV", Path(temp_dir) / "messages.csv"), \
                patch("m3t.repositories.csv_store.RECIPIENTS_CSV", Path(temp_dir) / "recipients.csv"), \
                patch("m3t.repositories.csv_store.TEMPLATES_DIR", Path(temp_dir) / "templates"), \
                patch("m3t.repositories.csv_store.BACKUPS_DIR", backup_dir):
                app = create_app()
                client = app.test_client()

                response = client.post(
                    "/api/dynamic-values",
                    json={"rows": [{"dynamic_key": "saludo", "value": "Hola", "enabled": "yes"}]},
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(DynamicValueService().list().rows[0]["dynamic_key"], "saludo")

    def test_preview_reports_missing_dynamic_values(self):
        app = create_app()
        client = app.test_client()
        with patch("m3t.services.dynamic_values.DynamicValueService.enabled_options", return_value={}):
            response = client.post(
                "/api/preview",
                json={
                    "template_id": "bienvenida",
                    "recipient_index": 0,
                    "message_format": "plain",
                    "subject": "Hola",
                    "body_text": "{dynamic.inexistente} {first_name}",
                    "body_html": "",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["missing_dynamic_values"], ["inexistente"])

    def test_attachment_paths_are_limited_to_attachments(self):
        self.assertEqual(safe_attachment_path("attachments/file.pdf").name, "file.pdf")
        self.assertEqual(safe_attachment_path("./attachments/file.pdf").name, "file.pdf")
        with self.assertRaises(ValueError):
            safe_attachment_path("templates/bienvenida.txt")
        with self.assertRaises(ValueError):
            safe_attachment_path("../credentials.json")

    def test_api_state_returns_recipient_ids(self):
        app = create_app()
        client = app.test_client()

        response = client.get("/api/state")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertNotIn("recipient_id", data["recipient_columns"])
        self.assertTrue(all("recipient_id" in row for row in data["recipients"]))

    def test_send_requires_confirmation(self):
        app = create_app()
        client = app.test_client()

        response = client.post("/api/send", json={"indexes": [0], "confirm": "NOPE"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["errors"], ["Confirmacion requerida."])

    def test_send_messages_waits_between_emails(self):
        messages = []
        for recipient in ("one@example.test", "two@example.test", "three@example.test"):
            message = EmailMessage()
            message["To"] = recipient
            message["From"] = "sender@example.com"
            message["Subject"] = "Test"
            message.set_content("Body")
            messages.append(message)

        sleeps = []
        results = send_messages(
            messages,
            service=FakeGmailService(),
            delay_seconds=1.5,
            sleeper=sleeps.append,
        )

        self.assertEqual([result["id"] for result in results], ["message-1", "message-2", "message-3"])
        self.assertEqual(sleeps, [1.5, 1.5])

    def test_home_serves_static_template_links(self):
        app = create_app()
        client = app.test_client()

        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("static/css/app.css", html)
        self.assertIn("static/js/state.js", html)


if __name__ == "__main__":
    unittest.main()
