from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import uuid
import threading
import time

app = Flask(__name__)
CORS(app)

# In-memory notice storage with metadata
notices = []
notice_lock = threading.Lock()  # Thread safety for concurrent requests

# System statistics (demonstrates distributed system monitoring)
stats = {
    "total_notices_created": 0,
    "total_requests": 0,
    "auto_cleanups": 0,
    "last_cleanup": None
}


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Hostel Notice Board API running",
        "version": "1.0",
        "endpoints": {
            "GET /notices": "Retrieve all active notices",
            "POST /notices": "Add a new notice",
            "GET /stats": "System statistics"
        }
    })


@app.route("/stats", methods=["GET"])
def get_stats():
    """Monitoring endpoint - important for distributed systems"""
    with notice_lock:
        return jsonify({
            **stats,
            "active_notices": len(notices),
            "server_time": datetime.now().isoformat()
        })


def cleanup_expired_notices():
    """Background cleanup task - demonstrates async operations"""
    global notices
    now = datetime.now()
    
    with notice_lock:  # Thread-safe access
        initial_count = len(notices)
        valid_notices = []

        for n in notices:
            try:
                expiry = datetime.fromisoformat(n["expires_at"])
                if expiry > now:
                    valid_notices.append(n)
            except Exception:
                pass

        notices = valid_notices
        
        cleaned = initial_count - len(notices)
        if cleaned > 0:
            stats["auto_cleanups"] += 1
            stats["last_cleanup"] = datetime.now().isoformat()
            print(f"[CLEANUP] Removed {cleaned} expired notices")


def auto_cleanup_worker():
    """Background thread for automatic cleanup"""
    while True:
        time.sleep(60)  # Clean every 60 seconds
        cleanup_expired_notices()


@app.route("/notices", methods=["POST"])
def add_notice():
    stats["total_requests"] += 1
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
        expiry = datetime.fromisoformat(expires_at)
        if expiry <= datetime.now():
            return jsonify({"error": "Expiry time must be in the future"}), 400
    except Exception:
        return jsonify({"error": "Invalid expiry datetime format"}), 400

    # Thread-safe insertion with unique ID
    with notice_lock:
        notice = {
            "id": str(uuid.uuid4()),  # Unique identifier
            "title": title,
            "message": message,
            "date": date,
            "expires_at": expires_at,
            "created_at": datetime.now().isoformat()  # Timestamp
        }
        notices.append(notice)
        stats["total_notices_created"] += 1

    print(f"[NOTICE ADDED] ID: {notice['id']}, Title: {title}")
    return jsonify({
        "message": "Notice added successfully",
        "notice_id": notice["id"]
    }), 201


@app.route("/notices", methods=["GET"])
def get_notices():
    stats["total_requests"] += 1
    cleanup_expired_notices()
    
    with notice_lock:  # Thread-safe read
        # Sort by creation time, newest first
        sorted_notices = sorted(
            notices, 
            key=lambda x: x.get("created_at", ""), 
            reverse=True
        )
        
    return jsonify(sorted_notices), 200


if __name__ == "__main__":
    # Start background cleanup thread
    cleanup_thread = threading.Thread(target=auto_cleanup_worker, daemon=True)
    cleanup_thread.start()
    print("[SERVER] Background cleanup worker started")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
