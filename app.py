# app.py
import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from rag_pipeline import handle_query, load_or_create_vectorstore, build_vectorstore

app = Flask(__name__, static_folder="static", template_folder="templates")

# Ensure vectorstore is loaded on startup
try:
    load_or_create_vectorstore()
except Exception as e:
    # Print the error but allow app to start so you can debug.
    print("Warning: vector store load/create failed on startup:", str(e))

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
        # Standardize return so front-end can parse
        return jsonify({"ok": True, "query": q, "result": result})
    except Exception as e:
        # Return error message (avoid leaking secrets)
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/rebuild_index", methods=["POST"])
def api_rebuild_index():
    # This endpoint should be protected in production (auth). For dev it's open.
    try:
        db = build_vectorstore(force_rebuild=True)
        return jsonify({"ok": True, "message": "FAISS index rebuilt", "docs_loaded": getattr(db, "index", "unknown")})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# Static files route if needed (Flask serves static by default from static/)
@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
