# app.py
import os
import threading
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

# Heavy imports kept, but we won't call them at import/startup
from rag_pipeline import handle_query, load_or_create_vectorstore, build_vectorstore

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# ---------- HEALTH ----------
@app.route("/healthz")
def healthz():
    return jsonify({"ok": True})

# ---------- OPTIONAL: LAZY PRELOAD ----------
_preload_started = False
_preload_lock = threading.Lock()

def _start_lazy_preload():
    """
    Kicks off a background preload AFTER the first incoming request.
    This ensures the server is already bound to $PORT when preload starts.
    """
    global _preload_started
    with _preload_lock:
        if _preload_started:
            return
        _preload_started = True
        try:
            threading.Thread(target=load_or_create_vectorstore, daemon=True).start()
            print("Vectorstore preload started in background (lazy).")
        except Exception as e:
            print("Failed to start background vectorstore loader:", e)

@app.before_request
def _maybe_warm():
    # Start a one-time lazy preload on first request only
    if not _preload_started:
        _start_lazy_preload()

# ----------------- ROUTES -----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/query", methods=["POST"])
def api_query():
    data = request.get_json(force=True)
    q = (data.get("q") or "").strip()
    if not q:
        return jsonify({"error": "Empty query"}), 400
    try:
        result = handle_query(q)  # inside this, your pipeline can load/build if missing
        return jsonify({"ok": True, "query": q, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/rebuild_index", methods=["POST"])
def api_rebuild_index():
    """
    CAUTION: Exposing rebuild publicly is risky.
    Protect this with an ADMIN_TOKEN in env if you keep it.
    """
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token and (request.headers.get("X-Admin-Token") != admin_token):
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        db = build_vectorstore(force_rebuild=True)
        return jsonify({
            "ok": True,
            "message": "FAISS index rebuilt successfully",
            "docs_loaded": getattr(db, "index", "unknown")
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)

# ----------------- ENTRY POINT -----------------
if __name__ == "__main__":
    # Bind to Render's injected PORT (falls back to 5000 locally)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
