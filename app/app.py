import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return "DeployGuard Nexus Application is Running"


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))

    app.run(host=host, port=port)