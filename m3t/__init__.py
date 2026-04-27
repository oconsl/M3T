from flask import Flask

from m3t.routes import api_config, api_mail, api_preview, api_recipients, api_templates, pages


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="web/templates",
        static_folder="web/static",
    )
    app.register_blueprint(pages.bp)
    app.register_blueprint(api_templates.bp)
    app.register_blueprint(api_recipients.bp)
    app.register_blueprint(api_preview.bp)
    app.register_blueprint(api_mail.bp)
    app.register_blueprint(api_config.bp)
    return app
