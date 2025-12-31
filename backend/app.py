from flask import Flask, request, jsonify
from datetime import datetime
import os



app = Flask(__name__)

# -------------------------
# In-memory notice storage
# -------------------------
notices = []  # Ephemeral state (cleared on restart)


# -------------------------
# Utility: Remove expired notices
# -------------------------
def cleanup_expired_notices():
    current_time = datetime.now()
    global notices

    notices = [
        notice for notice in notices
        if datetime.fromisoformat(notice["expires_at"]) > current_time
    ]


# -------------------------
# API: Add a new notice (Admin)
# -------------------------
@app.route("/notices", methods=["POST"])
def add_notice():
    data = request.get_json()

    required_fields = ["title", "message", "date", "expires_at"]
    if not all(field in data for field in required_fields):
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


# -------------------------
# API: Get active notices (Students)
# -------------------------
@app.route("/notices", methods=["GET"])
def get_notices():
    cleanup_expired_notices()
    return jsonify(notices), 200


# -------------------------
# Run server
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
# To run the server, use the command: python backend/app.py
# Ensure Flask is installed: pip install Flask