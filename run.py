from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)

    # Blueprints will be registered in Step 8
    return app


if __name__ == "__main__":
    app = create_app()
    print("Server is running on port 8080...")
    app.run(host="0.0.0.0", port=8080)
