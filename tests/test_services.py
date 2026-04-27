import unittest
from email.message import EmailMessage

from m3t import create_app
from m3t.services.mailer import send_messages
from m3t.services.formatting import extract_variables, normalize_message_format, normalize_send
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
            extract_variables("Hola {first_name}", "{{ignored}}", "{company}"),
            ["company", "first_name"],
        )

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
