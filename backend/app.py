from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from collections import defaultdict
import os
import uuid
import threading
import time
import signal
import sys

app = Flask(__name__)
CORS(app)

# Configuration
API_VERSION = "v1"
RATE_LIMIT = 10  # requests per minute
RATE_WINDOW = 60  # seconds

# In-memory storage
notices = []
notice_lock = threading.Lock()
request_tracker = defaultdict(list)
app.start_time = time.time()

# Statistics
stats = {
    "total_notices_created": 0,
    "total_requests": 0,
    "auto_cleanups": 0,
    "last_cleanup": None,
    "rate_limited_requests": 0
}


# ============= Rate Limiting =============
def check_rate_limit(client_ip):
    now = datetime.now()
    cutoff = now - timedelta(seconds=RATE_WINDOW)
    
    request_tracker[client_ip] = [
        req_time for req_time in request_tracker[client_ip] 
        if req_time > cutoff
    ]
    
    if len(request_tracker[client_ip]) >= RATE_LIMIT:
        stats["rate_limited_requests"] += 1
        return False
    
    request_tracker[client_ip].append(now)
    return True


# ============= Middleware =============
@app.before_request
def before_request():
    # Add request ID
    request.request_id = str(uuid.uuid4())
    print(f"[REQUEST {request.request_id}] {request.method} {request.path}")
    
    # Rate limiting
    client_ip = request.remote_addr
    if not check_rate_limit(client_ip):
        return jsonify({
            "error": "Rate limit exceeded",
            "message": f"Maximum {RATE_LIMIT} requests per minute",
            "request_id": request.request_id
        }), 429


@app.after_request
def after_request(response):
    # Add headers
    response.headers['X-Request-ID'] = request.request_id
    response.headers['X-API-Version'] = API_VERSION
    response.headers['X-Server'] = 'Hostel-Notice-Board'
    
    # Caching
    if request.method == "GET":
        response.headers['Cache-Control'] = 'public, max-age=30'
    else:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    
    print(f"[RESPONSE {request.request_id}] Status: {response.status_code}")
    return response


# ============= Helper Functions =============
def error_response(message, status_code, error_code=None):
    return jsonify({
        "error": True,
        "message": message,
        "error_code": error_code,
        "timestamp": datetime.now().isoformat(),
        "request_id": getattr(request, 'request_id', None)
    }), status_code


def cleanup_expired_notices():
    global notices
    now = datetime.now()
    
    with notice_lock:
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
    while True:
        time.sleep(60)
        cleanup_expired_notices()


# ============= Routes =============
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Hostel Notice Board API",
        "version": API_VERSION,
        "endpoints": {
            "GET /": "API information",
            "GET /health": "Health check",
            "GET /stats": "System statistics",
            "GET /notices": "Get all notices (supports ?search=, ?limit=, ?sort=)",
            "POST /notices": "Add new notice",
            "POST /notices/batch": "Add multiple notices",
            "PATCH /notices/<id>": "Update notice",
            "DELETE /notices/<id>": "Delete notice"
        }
    })


@app.route("/health", methods=["GET"])
def health_check():
    with notice_lock:
        is_healthy = True
        notice_count = len(notices)
    
    uptime_seconds = time.time() - app.start_time
    
    return jsonify({
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime_seconds, 2),
        "uptime_human": f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m",
        "notices_count": notice_count,
        "memory_usage_kb": round(len(str(notices)) / 1024, 2)
    }), 200 if is_healthy else 503


@app.route("/stats", methods=["GET"])
def get_stats():
    with notice_lock:
        return jsonify({
            **stats,
            "active_notices": len(notices),
            "server_time": datetime.now().isoformat(),
            "uptime_seconds": round(time.time() - app.start_time, 2)
        })


@app.route("/notices", methods=["GET"])
def get_notices():
    stats["total_requests"] += 1
    cleanup_expired_notices()
    
    search = request.args.get("search", "").lower()
    limit = request.args.get("limit", type=int)
    sort_by = request.args.get("sort", "created_at")
    
    with notice_lock:
        filtered = notices
        
        if search:
            filtered = [
                n for n in filtered 
                if search in n["title"].lower() or search in n["message"].lower()
            ]
        
        reverse = sort_by == "created_at"
        sorted_notices = sorted(
            filtered,
            key=lambda x: x.get(sort_by, ""),
            reverse=reverse
        )
        
        if limit and limit > 0:
            sorted_notices = sorted_notices[:limit]
    
    return jsonify({
        "total": len(sorted_notices),
        "notices": sorted_notices
    }), 200


@app.route("/notices", methods=["POST"])
def add_notice():
    stats["total_requests"] += 1
    data = request.get_json()

    if not data:
        return error_response("Invalid JSON payload", 400, "INVALID_JSON")

    title = data.get("title", "").strip()
    message = data.get("message", "").strip()
    date = data.get("date", "").strip()
    expires_at = data.get("expires_at", "").strip()

    if not all([title, message, date, expires_at]):
        return error_response("All fields are required", 400, "MISSING_FIELDS")

    try:
        expiry = datetime.fromisoformat(expires_at)
        if expiry <= datetime.now():
            return error_response("Expiry time must be in the future", 400, "INVALID_EXPIRY")
    except Exception:
        return error_response("Invalid expiry datetime format", 400, "INVALID_FORMAT")

    with notice_lock:
        notice = {
            "id": str(uuid.uuid4()),
            "title": title,
            "message": message,
            "date": date,
            "expires_at": expires_at,
            "created_at": datetime.now().isoformat()
        }
        notices.append(notice)
        stats["total_notices_created"] += 1

    print(f"[NOTICE ADDED] ID: {notice['id']}, Title: {title}")
    return jsonify({
        "message": "Notice added successfully",
        "notice_id": notice["id"],
        "notice": notice
    }), 201


@app.route("/notices/batch", methods=["POST"])
def add_notices_batch():
    stats["total_requests"] += 1
    data = request.get_json()
    
    if not isinstance(data, list):
        return error_response("Expected array of notices", 400, "INVALID_PAYLOAD")
    
    added_notices = []
    errors = []
    
    with notice_lock:
        for idx, notice_data in enumerate(data):
            try:
                title = notice_data.get("title", "").strip()
                message = notice_data.get("message", "").strip()
                date = notice_data.get("date", "").strip()
                expires_at = notice_data.get("expires_at", "").strip()
                
                if not all([title, message, date, expires_at]):
                    errors.append({"index": idx, "error": "Missing fields"})
                    continue
                
                expiry = datetime.fromisoformat(expires_at)
                if expiry <= datetime.now():
                    errors.append({"index": idx, "error": "Expiry in past"})
                    continue
                
                notice = {
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "message": message,
                    "date": date,
                    "expires_at": expires_at,
                    "created_at": datetime.now().isoformat()
                }
                notices.append(notice)
                added_notices.append(notice["id"])
                stats["total_notices_created"] += 1
                
            except Exception as e:
                errors.append({"index": idx, "error": str(e)})
    
    return jsonify({
        "message": f"Added {len(added_notices)} notices",
        "added": added_notices,
        "errors": errors if errors else None
    }), 201 if added_notices else 400


@app.route("/notices/<notice_id>", methods=["PATCH"])
def update_notice(notice_id):
    stats["total_requests"] += 1
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", 400, "NO_DATA")
    
    with notice_lock:
        for notice in notices:
            if notice["id"] == notice_id:
                if "title" in data:
                    notice["title"] = data["title"].strip()
                if "message" in data:
                    notice["message"] = data["message"].strip()
                if "expires_at" in data:
                    try:
                        expiry = datetime.fromisoformat(data["expires_at"])
                        if expiry <= datetime.now():
                            return error_response("Expiry must be in future", 400)
                        notice["expires_at"] = data["expires_at"]
                    except:
                        return error_response("Invalid datetime", 400)
                
                notice["updated_at"] = datetime.now().isoformat()
                return jsonify({
                    "message": "Notice updated",
                    "notice": notice
                }), 200
        
        return error_response("Notice not found", 404, "NOT_FOUND")


@app.route("/notices/<notice_id>", methods=["DELETE"])
def delete_notice(notice_id):
    stats["total_requests"] += 1
    
    with notice_lock:
        for i, notice in enumerate(notices):
            if notice["id"] == notice_id:
                deleted = notices.pop(i)
                print(f"[NOTICE DELETED] ID: {notice_id}")
                return jsonify({
                    "message": "Notice deleted",
                    "deleted_notice": deleted
                }), 200
        
        return error_response("Notice not found", 404, "NOT_FOUND")


# ============= Graceful Shutdown =============
def graceful_shutdown(signum, frame):
    print("\n[SHUTDOWN] Graceful shutdown initiated...")
    
    with notice_lock:
        print(f"[SHUTDOWN] Active notices: {len(notices)}")
        print(f"[SHUTDOWN] Total created: {stats['total_notices_created']}")
        print(f"[SHUTDOWN] Total requests: {stats['total_requests']}")
        print(f"[SHUTDOWN] Rate limited: {stats['rate_limited_requests']}")
    
    sys.exit(0)


signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)


# ============= Main =============
if __name__ == "__main__":
    # Start background cleanup
    cleanup_thread = threading.Thread(target=auto_cleanup_worker, daemon=True)
    cleanup_thread.start()
    print(f"[SERVER] Background cleanup worker started")
    print(f"[SERVER] API Version: {API_VERSION}")
    print(f"[SERVER] Rate limit: {RATE_LIMIT} requests per {RATE_WINDOW}s")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)