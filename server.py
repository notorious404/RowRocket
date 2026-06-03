# server.py  — Flask REST API wrapper for the Table Extraction backend
# All original Python files (app.py, pdf_table_extractor.py, etc.) remain UNTOUCHED.
# This file ONLY adds a REST API layer consumed by index.html.

import os
import io
import json
import csv
import tempfile
import secrets
import re
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import List, Dict, Any

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth
    from firebase_admin import credentials, firestore
except ImportError:
    firebase_admin = None
    firebase_auth = None
    credentials = None
    firestore = None

from pdf_doc_loader import save_and_read_uploaded_files, extract_docx_tables
from pdf_table_extractor import TableExtractor
from table_pdf_report import TableReportGenerator
from utils import ensure_directories, build_report_name

app = Flask(__name__, static_folder=".", static_url_path="/static")
CORS(app)

"""
FIREBASE BACKEND CREDENTIALS GO HERE LATER
When you switch Flask to Firebase Admin, do not paste the service account JSON
directly into this file. Use one of these safer options:

1. Local testing:
   Save the private key file as firebase-service-account.json in this folder.
   Keep it out of GitHub using .gitignore.

2. Deployment:
   Put Firebase Admin credentials in Render/Railway environment variables.

Example future setup:
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred)

Never upload firebase-service-account.json, private_key, or .env to GitHub.
"""

AUTH_DB_PATH = os.path.join(".", "auth_data.json")
FIREBASE_SERVICE_ACCOUNT_PATH = os.path.join(".", "firebase-service-account.json")
FREE_UNVERIFIED_USES = 4
EMAIL_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")
firebase_db = None


def _init_firebase_admin():
    """Initialize Firebase Admin from env JSON or local service account file."""
    global firebase_db
    if firebase_admin is None or firebase_admin._apps:
        if firebase_admin is not None and firebase_admin._apps and firebase_db is None:
            firebase_db = firestore.client()
        return firebase_db is not None

    service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        cred = credentials.Certificate(json.loads(service_account_json))
    elif os.path.exists(FIREBASE_SERVICE_ACCOUNT_PATH):
        cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_PATH)
    else:
        return False

    firebase_admin.initialize_app(cred)
    firebase_db = firestore.client()
    return True


_init_firebase_admin()


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _load_auth_db():
    if not os.path.exists(AUTH_DB_PATH):
        return {"users": {}, "sessions": {}}
    with open(AUTH_DB_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_auth_db(db):
    with open(AUTH_DB_PATH, "w", encoding="utf-8") as fh:
        json.dump(db, fh, indent=2)


def _public_user(user):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "email_verified": user.get("email_verified", False),
        "unverified_uses": user.get("unverified_uses", 0),
        "free_unverified_uses": FREE_UNVERIFIED_USES,
        "theme_preference": user.get("theme_preference", "dark"),
        "created_at": user.get("created_at"),
    }


def _find_user_by_email(db, email):
    email = (email or "").strip().lower()
    for user in db["users"].values():
        if user["email"].lower() == email:
            return user
    return None


def _log_auth(user, action, request_obj):
    user.setdefault("auth_history", []).insert(0, {
        "action": action,
        "at": _now_iso(),
        "ip": request_obj.headers.get("X-Forwarded-For", request_obj.remote_addr or "unknown"),
        "user_agent": request_obj.headers.get("User-Agent", "unknown"),
    })
    user["auth_history"] = user["auth_history"][:50]


def _new_otp(user, purpose, new_email=None):
    code = f"{secrets.randbelow(900000) + 100000}"
    user["pending_otp"] = {
        "code": code,
        "purpose": purpose,
        "new_email": new_email,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    }
    return code


def _require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
        firebase_user = _get_firebase_user(token)
        if firebase_user:
            request.auth_provider = "firebase"
            request.firebase_user = firebase_user
            request.current_user = firebase_user["profile"]
            return fn(*args, **kwargs)

        if token and firebase_db is None:
            request.auth_provider = "local_unverified_firebase"
            request.current_user = {
                "id": "firebase-local",
                "email_verified": True,
                "unverified_uses": 0,
                "free_unverified_uses": FREE_UNVERIFIED_USES,
            }
            return fn(*args, **kwargs)

        db = _load_auth_db()
        session = db["sessions"].get(token)
        if not token or not session:
            return jsonify({"error": "Please sign in first."}), 401
        user = db["users"].get(session["user_id"])
        if not user:
            return jsonify({"error": "Session user was not found."}), 401
        request.auth_db = db
        request.auth_token = token
        request.current_user = user
        return fn(*args, **kwargs)
    return wrapper


def _get_optional_auth():
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        return None, None, None
    firebase_user = _get_firebase_user(token)
    if firebase_user:
        return "firebase", firebase_user, None
    if firebase_db is None:
        return "local_unverified_firebase", {
            "id": "firebase-local",
            "email_verified": True,
            "unverified_uses": 0,
            "free_unverified_uses": FREE_UNVERIFIED_USES,
        }, None
    db = _load_auth_db()
    session = db["sessions"].get(token)
    if not session:
        return None, None, None
    user = db["users"].get(session["user_id"])
    if not user:
        return None, None, None
    return "local", user, db


def _get_firebase_user(token):
    if not token or firebase_auth is None or firebase_db is None:
        return None
    try:
        decoded = firebase_auth.verify_id_token(token)
        uid = decoded["uid"]
        user_ref = firebase_db.collection("users").document(uid)
        snapshot = user_ref.get()
        profile = snapshot.to_dict() or {}
        return {
            "uid": uid,
            "decoded": decoded,
            "ref": user_ref,
            "profile": {
                "id": uid,
                "name": profile.get("name") or decoded.get("email", "User"),
                "email": decoded.get("email") or profile.get("email", ""),
                "email_verified": decoded.get("email_verified", False),
                "unverified_uses": profile.get("unverified_uses", 0),
                "free_unverified_uses": profile.get("free_unverified_uses", FREE_UNVERIFIED_USES),
                "theme_preference": profile.get("theme_preference", "dark"),
            },
        }
    except Exception:
        return None


def _consume_firebase_unverified_use(firebase_user):
    profile = firebase_user["profile"]
    if profile.get("email_verified"):
        return None
    used = int(profile.get("unverified_uses", 0))
    limit = int(profile.get("free_unverified_uses", FREE_UNVERIFIED_USES))
    if used >= limit:
        return jsonify({
            "error": "Email verification required. You have used all 4 free unverified extractions.",
            "requires_verification": True,
        }), 403
    new_used = used + 1
    firebase_user["ref"].set({"unverified_uses": new_used}, merge=True)
    profile["unverified_uses"] = new_used
    return limit - new_used


def _validate_email(email):
    return bool(EMAIL_PATTERN.match(email or ""))


def _validate_password(password):
    return bool(PASSWORD_PATTERN.match(password or ""))


def _consume_unverified_use(db, user):
    if user.get("email_verified"):
        return None
    used = user.get("unverified_uses", 0)
    if used >= FREE_UNVERIFIED_USES:
        return jsonify({
            "error": "Email verification required. You have used all 4 free unverified extractions.",
            "requires_verification": True,
        }), 403
    user["unverified_uses"] = used + 1
    _save_auth_db(db)
    remaining = FREE_UNVERIFIED_USES - user["unverified_uses"]
    if remaining >= 0:
        return remaining
    return 0


@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not name:
        return jsonify({"error": "Name is required."}), 400
    if not _validate_email(email):
        return jsonify({"error": "Enter a valid email. Email must not start with a number."}), 400
    if not _validate_password(password):
        return jsonify({"error": "Password must be at least 8 characters with uppercase, lowercase, number, and special character."}), 400

    db = _load_auth_db()
    if _find_user_by_email(db, email):
        return jsonify({"error": "An account with this email already exists."}), 409

    user_id = secrets.token_urlsafe(12)
    user = {
        "id": user_id,
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password),
        "email_verified": False,
        "unverified_uses": 0,
        "theme_preference": data.get("theme_preference") if data.get("theme_preference") in ["dark", "light"] else "dark",
        "created_at": _now_iso(),
        "auth_history": [],
    }
    otp = _new_otp(user, "verify_email")
    _log_auth(user, "signup", request)
    token = secrets.token_urlsafe(32)
    db["users"][user_id] = user
    db["sessions"][token] = {"user_id": user_id, "created_at": _now_iso()}
    _save_auth_db(db)
    return jsonify({"token": token, "user": _public_user(user), "otp_dev": otp})


@app.route("/api/auth/signin", methods=["POST"])
def signin():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    db = _load_auth_db()
    user = _find_user_by_email(db, email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401
    token = secrets.token_urlsafe(32)
    db["sessions"][token] = {"user_id": user["id"], "created_at": _now_iso()}
    _log_auth(user, "signin", request)
    _save_auth_db(db)
    return jsonify({"token": token, "user": _public_user(user)})


@app.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    if not _validate_email(email):
        return jsonify({"error": "Enter a valid email. Email must not start with a number."}), 400

    db = _load_auth_db()
    user = _find_user_by_email(db, email)
    if not user:
        return jsonify({"error": "No account was found with this email."}), 404
    otp = _new_otp(user, "reset_password")
    _log_auth(user, "password_reset_requested", request)
    _save_auth_db(db)
    return jsonify({"ok": True, "otp_dev": otp})


@app.route("/api/auth/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    code = str(data.get("otp", "")).strip()
    password = data.get("password") or ""
    if not _validate_email(email):
        return jsonify({"error": "Enter a valid email. Email must not start with a number."}), 400
    if not _validate_password(password):
        return jsonify({"error": "Password must be at least 8 characters with uppercase, lowercase, number, and special character."}), 400

    db = _load_auth_db()
    user = _find_user_by_email(db, email)
    pending = (user or {}).get("pending_otp") or {}
    if not user or pending.get("purpose") != "reset_password" or pending.get("code") != code:
        return jsonify({"error": "Invalid password reset code."}), 400
    if datetime.fromisoformat(pending["expires_at"]) < datetime.now(timezone.utc):
        return jsonify({"error": "Password reset code expired."}), 400
    user["password_hash"] = generate_password_hash(password)
    user.pop("pending_otp", None)
    _log_auth(user, "password_reset", request)
    _save_auth_db(db)
    return jsonify({"ok": True})


@app.route("/api/auth/me", methods=["GET"])
@_require_auth
def me():
    return jsonify({"user": _public_user(request.current_user)})


@app.route("/api/auth/logout", methods=["POST"])
@_require_auth
def logout():
    db = request.auth_db
    db["sessions"].pop(request.auth_token, None)
    _log_auth(request.current_user, "logout", request)
    _save_auth_db(db)
    return jsonify({"ok": True})


@app.route("/api/auth/send-otp", methods=["POST"])
@_require_auth
def send_otp():
    db = request.auth_db
    otp = _new_otp(request.current_user, "verify_email")
    _log_auth(request.current_user, "otp_requested", request)
    _save_auth_db(db)
    return jsonify({"ok": True, "otp_dev": otp})


@app.route("/api/auth/verify-email", methods=["POST"])
@_require_auth
def verify_email():
    code = str((request.get_json() or {}).get("otp", "")).strip()
    user = request.current_user
    pending = user.get("pending_otp") or {}
    if pending.get("purpose") != "verify_email" or pending.get("code") != code:
        return jsonify({"error": "Invalid verification code."}), 400
    if datetime.fromisoformat(pending["expires_at"]) < datetime.now(timezone.utc):
        return jsonify({"error": "Verification code expired."}), 400
    user["email_verified"] = True
    user.pop("pending_otp", None)
    _log_auth(user, "email_verified", request)
    _save_auth_db(request.auth_db)
    return jsonify({"user": _public_user(user)})


@app.route("/api/auth/change-email", methods=["POST"])
@_require_auth
def change_email():
    data = request.get_json() or {}
    new_email = (data.get("email") or "").strip().lower()
    if not _validate_email(new_email):
        return jsonify({"error": "Enter a valid email. Email must not start with a number."}), 400
    db = request.auth_db
    existing = _find_user_by_email(db, new_email)
    if existing and existing["id"] != request.current_user["id"]:
        return jsonify({"error": "That email is already in use."}), 409
    otp = _new_otp(request.current_user, "change_email", new_email=new_email)
    _log_auth(request.current_user, "email_change_requested", request)
    _save_auth_db(db)
    return jsonify({"ok": True, "otp_dev": otp})


@app.route("/api/auth/confirm-email-change", methods=["POST"])
@_require_auth
def confirm_email_change():
    code = str((request.get_json() or {}).get("otp", "")).strip()
    user = request.current_user
    pending = user.get("pending_otp") or {}
    if pending.get("purpose") != "change_email" or pending.get("code") != code:
        return jsonify({"error": "Invalid email change code."}), 400
    if datetime.fromisoformat(pending["expires_at"]) < datetime.now(timezone.utc):
        return jsonify({"error": "Email change code expired."}), 400
    user["email"] = pending["new_email"]
    user["email_verified"] = True
    user.pop("pending_otp", None)
    _log_auth(user, "email_changed", request)
    _save_auth_db(request.auth_db)
    return jsonify({"user": _public_user(user)})


@app.route("/api/auth/history", methods=["GET"])
@_require_auth
def auth_history():
    return jsonify({"history": request.current_user.get("auth_history", [])})


@app.route("/api/auth/settings", methods=["PATCH"])
@_require_auth
def update_settings():
    data = request.get_json() or {}
    theme = data.get("theme_preference")
    if theme is not None:
        if theme not in ["dark", "light"]:
            return jsonify({"error": "Theme must be dark or light."}), 400
        request.current_user["theme_preference"] = theme
        _log_auth(request.current_user, "theme_changed", request)
    _save_auth_db(request.auth_db)
    return jsonify({"user": _public_user(request.current_user)})


@app.route("/api/auth/delete-account", methods=["DELETE"])
@_require_auth
def delete_account():
    db = request.auth_db
    user_id = request.current_user["id"]
    db["users"].pop(user_id, None)
    db["sessions"] = {k: v for k, v in db["sessions"].items() if v["user_id"] != user_id}
    _save_auth_db(db)
    return jsonify({"ok": True})

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

    auth_provider, current_user, auth_db = _get_optional_auth()
    anonymous_trial = request.headers.get("X-Anonymous-Trial") == "1"
    usage_state = None
    if auth_provider == "firebase":
        usage_state = _consume_firebase_unverified_use(current_user)
        current_user = current_user["profile"]
        if not isinstance(usage_state, int) and usage_state is not None:
            return usage_state
    elif auth_provider == "local_unverified_firebase":
        usage_state = None
    elif auth_provider == "local":
        usage_state = _consume_unverified_use(auth_db, current_user)
        if not isinstance(usage_state, int) and usage_state is not None:
            return usage_state
    elif not anonymous_trial:
        return jsonify({"error": "Please sign up and sign in to continue."}), 401

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
        ext = os.path.splitext(path)[1].lower()
        if ext == ".docx":
            direct_tables = extract_docx_tables(path)
            if direct_tables:
                all_tables.extend(direct_tables)
                continue

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

    response = {
        "tables": all_tables,
        "report_path": report_path,
        "table_count": len(all_tables),
    }
    if isinstance(usage_state, int):
        response["unverified_uses_remaining"] = usage_state
    if anonymous_trial and not current_user:
        response["anonymous_trial_used"] = True
    return jsonify(response)


@app.route("/api/download-report", methods=["GET"])
def download_report():
    """Download the generated PDF report."""
    path = request.args.get("path", "")
    if not path or not os.path.isfile(path):
        return jsonify({"error": "Report not found"}), 404
    safe_root = os.path.abspath("output_reports")
    requested = os.path.abspath(path)
    if not requested.startswith(safe_root):
        return jsonify({"error": "Invalid report path"}), 400
    return send_file(
        path,
        as_attachment=True,
        download_name=os.path.basename(path),
        mimetype="application/pdf",
    )


@app.route("/api/download-csv", methods=["POST"])
@_require_auth
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
    app.run(debug=False, use_reloader=False, host="0.0.0.0", port=5000)
