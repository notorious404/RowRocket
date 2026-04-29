# server.py  — Flask REST API wrapper for the Table Extraction backend
# All original Python files (app.py, pdf_table_extractor.py, etc.) remain UNTOUCHED.
# This file ONLY adds a REST API layer consumed by index.html.

import os
import io
import json
import csv
import tempfile
from typing import List, Dict, Any

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

from pdf_doc_loader import save_and_read_uploaded_files
from pdf_table_extractor import TableExtractor
from table_pdf_report import TableReportGenerator
from utils import ensure_directories, build_report_name

app = Flask(__name__, static_folder=".", static_url_path="/static")
CORS(app)

# ── Serve frontend ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(".", filename)

# ── Core extraction endpoint ──────────────────────────────────────────────────

@app.route("/api/extract", methods=["POST"])
def extract():
    """
    Accepts multipart/form-data with one or more files.
    Returns JSON: { tables: [...], report_path: "..." }
    """
    if "files" not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    uploaded_files = request.files.getlist("files")
    if not uploaded_files or all(f.filename == "" for f in uploaded_files):
        return jsonify({"error": "No files selected"}), 400

    ensure_directories()

    # Wrap Flask FileStorage objects to look like Streamlit UploadedFile
    class _FakeUploadedFile:
        def __init__(self, fs):
            self.name = fs.filename
            self._data = fs.read()
        def read(self):
            return self._data

    fake_files = [_FakeUploadedFile(f) for f in uploaded_files]

    # --- Step 1: Save & read ---
    file_texts = save_and_read_uploaded_files(fake_files)

    # --- Step 2: Extract tables ---
    extractor = TableExtractor()
    all_tables: List[Dict[str, Any]] = []
    for path, text in file_texts.items():
        if not text.strip():
            continue
        fname = os.path.basename(path)
        tables = extractor.extract_tables_from_text(fname, text)
        all_tables.extend(tables)

    # --- Step 3: Generate PDF report ---
    pdf_names = [f.name for f in fake_files]
    report_path = build_report_name(pdf_names, suffix="TABLES")
    report_generator = TableReportGenerator(output_path=report_path)
    report_generator.build(all_tables)

    return jsonify({
        "tables": all_tables,
        "report_path": report_path,
        "table_count": len(all_tables),
    })


@app.route("/api/download-report", methods=["GET"])
def download_report():
    """Download the generated PDF report."""
    path = request.args.get("path", "")
    if not path or not os.path.isfile(path):
        return jsonify({"error": "Report not found"}), 404
    return send_file(
        path,
        as_attachment=True,
        download_name=os.path.basename(path),
        mimetype="application/pdf",
    )


@app.route("/api/download-csv", methods=["POST"])
def download_csv():
    """Convert a table (sent as JSON) to CSV and return it."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    headers = data.get("headers", [])
    rows = data.get("rows", [])

    output = io.StringIO()
    writer = csv.writer(output)
    if headers:
        writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        as_attachment=True,
        download_name="table.csv",
        mimetype="text/csv",
    )


if __name__ == "__main__":
    ensure_directories()
    app.run(debug=True, host="0.0.0.0", port=5000)
