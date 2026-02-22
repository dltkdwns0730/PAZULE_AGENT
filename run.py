from flask import Flask
from flask_cors import CORS

from app.api.routes import api
from app.core.config import settings


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(api)

    return app


if __name__ == "__main__":
    app = create_app()
    print(f"{settings.PROJECT_NAME} v{settings.VERSION} 서버 실행 중 (포트 8080)...")
    app.run(host="0.0.0.0", port=8080)
