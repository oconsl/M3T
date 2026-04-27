import unittest

from mail_mcp import create_app
from mail_mcp.services.formatting import extract_variables, normalize_message_format, normalize_send
from mail_mcp.services.recipients import safe_attachment_path


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
