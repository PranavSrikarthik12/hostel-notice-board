from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# In-memory notice storage
notices = []


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Hostel Notice Board API running",
        "endpoints": ["/notices"]
    })


def cleanup_expired_notices():
    global notices
    now = datetime.now()
    valid_notices = []

    for n in notices:
        try:
            expiry = datetime.fromisoformat(n["expires_at"])
            if expiry > now:
                valid_notices.append(n)
        except Exception:
            # If parsing fails, drop the notice
            pass

    notices = valid_notices


@app.route("/notices", methods=["POST"])
def add_notice():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    title = data.get("title", "").strip()
    message = data.get("message", "").strip()
    date = data.get("date", "").strip()
    expires_at = data.get("expires_at", "").strip()

    if not all([title, message, date, expires_at]):
        return jsonify({"error": "All fields are required"}), 400

    try:
        # Validate expiry format
        datetime.fromisoformat(expires_at)
    except Exception:
        return jsonify({"error": "Invalid expiry datetime format"}), 400

    notice = {
        "title": title,
        "message": message,
        "date": date,
        "expires_at": expires_at
    }

    notices.append(notice)

    return jsonify({"message": "Notice added successfully"}), 201


@app.route("/notices", methods=["GET"])
def get_notices():
    cleanup_expired_notices()
    return jsonify(notices), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
