# app.py
import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from rag_pipeline import handle_query, load_or_create_vectorstore, build_vectorstore

app = Flask(__name__, static_folder="static", template_folder="templates")

# ---------------------------------------------------------------------
#  Load or rebuild FAISS vectorstore at runtime (lightweight startup)
# ---------------------------------------------------------------------
try:
    print("🔹 Checking for existing FAISS index...")
    db = load_or_create_vectorstore()
    if not db:
        print("⚠️ No FAISS index found — building new one.")
        build_vectorstore(force_rebuild=True)
    else:
        print("✅ FAISS index loaded successfully.")
except Exception as e:
    print(f"⚠️ Warning: could not load vectorstore — will rebuild on first query. ({e})")

# ---------------------------------------------------------------------
#  Routes
# ---------------------------------------------------------------------

@app.route("/")
def index():
    """Render the chatbot UI."""
    return render_template("index.html")


@app.route("/api/query", methods=["POST"])
def api_query():
    """Handle chat queries from the frontend."""
    data = request.get_json(force=True)
    q = data.get("q", "").strip()
    if not q:
        return jsonify({"error": "Empty query"}), 400

    try:
        result = handle_query(q)
        return jsonify({"ok": True, "query": q, "result": result})
    except Exception as e:
        # Avoid leaking stack traces or secrets
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/rebuild_index", methods=["POST"])
def api_rebuild_index():
    """Force a rebuild of the FAISS index (for dev use only)."""
    try:
        build_vectorstore(force_rebuild=True)
        return jsonify({"ok": True, "message": "FAISS index rebuilt successfully."})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/static/<path:path>")
def send_static(path):
    """Serve static files (Flask default)."""
    return send_from_directory("static", path)


# ---------------------------------------------------------------------
#  Run app
# ---------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    print(f"🚀 Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
