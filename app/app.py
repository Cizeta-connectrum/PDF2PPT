import os
import shutil
import tempfile
import uuid

from flask import Flask, after_this_request, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename

import storage
from converter import convert_pdf_to_pptx

# Cloud Run's front-end enforces a hard 32 MB request body limit, so keep
# our own limit comfortably under that (accounting for multipart overhead).
MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


@app.errorhandler(413)
def handle_too_large(_exc):
    return jsonify({"error": "ファイルサイズが大きすぎます(上限25MB)。"}), 413


def _is_pdf(file_storage) -> bool:
    if not file_storage or not file_storage.filename:
        return False
    if not file_storage.filename.lower().endswith(".pdf"):
        return False
    header = file_storage.stream.read(5)
    file_storage.stream.seek(0)
    return header == b"%PDF-"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/apps", methods=["GET"])
def list_apps():
    try:
        return jsonify(storage.list_apps())
    except storage.StorageError as exc:
        return jsonify({"error": str(exc)}), 502


@app.route("/convert", methods=["POST"])
def convert():
    uploaded = request.files.get("pdf_file")
    mode = request.form.get("mode", "image")
    if mode not in ("image", "editable"):
        return jsonify({"error": "無効な変換モードです。"}), 400
    if not _is_pdf(uploaded):
        return jsonify({"error": "有効なPDFファイルをアップロードしてください。"}), 400

    workdir = tempfile.mkdtemp(prefix="pdf2ppt_")
    safe_name = secure_filename(uploaded.filename) or "input.pdf"
    base_name = os.path.splitext(safe_name)[0] or "presentation"
    pdf_path = os.path.join(workdir, f"{uuid.uuid4().hex}.pdf")
    pptx_path = os.path.join(workdir, f"{uuid.uuid4().hex}.pptx")

    uploaded.save(pdf_path)

    try:
        convert_pdf_to_pptx(pdf_path, pptx_path, mode=mode)
    except Exception as exc:
        shutil.rmtree(workdir, ignore_errors=True)
        return jsonify({"error": f"変換に失敗しました: {exc}"}), 500

    @after_this_request
    def cleanup(response):
        shutil.rmtree(workdir, ignore_errors=True)
        return response

    download_name = f"{base_name}.pptx"
    return send_file(
        pptx_path,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
