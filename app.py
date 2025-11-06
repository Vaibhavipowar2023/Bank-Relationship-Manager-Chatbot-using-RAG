# app.py
import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from rag_pipeline import handle_query, load_or_create_vectorstore, build_vectorstore
from flask_cors import CORS
import threading

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)  # Enable CORS for frontend (Vercel)

# Load vectorstore on startup (non-blocking)
try:
    load_or_create_vectorstore()
except Exception as e:
    print("Warning: vector store load/create failed on startup:", str(e))

# ✅ Start vectorstore preload in background right after app init
def start_preload():
    try:
        threading.Thread(target=load_or_create_vectorstore, daemon=True).start()
        print("Vectorstore preload started in background.")
    except Exception as e:
        print("Failed to start background vectorstore loader:", e)

start_preload()  # immediately start preload thread


# ----------------- ROUTES -----------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/query", methods=["POST"])
def api_query():
    data = request.get_json(force=True)
    q = data.get("q", "").strip()
    if not q:
        return jsonify({"error": "Empty query"}), 400

    try:
        result = handle_query(q)
        return jsonify({"ok": True, "query": q, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/rebuild_index", methods=["POST"])
def api_rebuild_index():
    """Force rebuild the FAISS vectorstore (use only for debugging)."""
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
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
