import hmac
import secrets

from flask import jsonify, request, session

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def get_or_create_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def csrf_protect():
    if request.method in SAFE_METHODS:
        return None
    expected = session.get("csrf_token")
    sent = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    if not expected or not sent or not hmac.compare_digest(expected, sent):
        return jsonify({"error": "Недействительный CSRF-токен"}), 403
    return None
