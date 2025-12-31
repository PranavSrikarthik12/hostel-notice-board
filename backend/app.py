from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# In-memory notice storage (ephemeral)
notices = []


# Utility: Remove expired notices (TTL cleanup)
def cleanup_expired_notices():
    global notices
    now = datetime.now()
    notices = [
        n for n in notices
        if datetime.fromisoformat(n["expires_at"]) > now
    ]


# API: Add notice (Admin)
@app.route("/notices", methods=["POST"])
def add_notice():
    data = request.get_json()

    required_fields = ["title", "message", "date", "expires_at"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    notice = {
        "title": data["title"],
        "message": data["message"],
        "date": data["date"],
        "expires_at": data["expires_at"]
    }

    notices.append(notice)

    return jsonify({
        "status": "success",
        "message": "Notice added successfully"
    }), 201


# API: Get active notices (Students)
@app.route("/notices", methods=["GET"])
def get_notices():
    cleanup_expired_notices()
    return jsonify(notices), 200


# Run app (Render-compatible)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
