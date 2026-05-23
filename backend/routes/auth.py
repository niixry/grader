from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from decorators import login_required
from models import User, db
import hmac
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/register", methods=["POST"])
def register():
    data        = request.get_json()
    email       = (data.get("email") or "").strip().lower()
    password    = data.get("password") or ""
    invite_code = (data.get("invite_code") or "").strip()

    if not Config.INVITE_CODE:
        return jsonify({"error": "Регистрация закрыта"}), 403
    if not invite_code or not hmac.compare_digest(invite_code, Config.INVITE_CODE):
        return jsonify({"error": "Неверный код приглашения"}), 403

    if not email or not password:
        return jsonify({"error": "Введите email и пароль"}), 400
    if len(password) < 6:
        return jsonify({"error": "Пароль должен быть не менее 6 символов"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Пользователь с таким email уже существует"}), 409

    user = User(email=email, password_hash=generate_password_hash(password))
    db.session.add(user)
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500

    session["user_id"] = user.id
    session["email"]   = email
    return jsonify({"email": email})


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data     = request.get_json()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Введите email и пароль"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Неверный email или пароль"}), 401

    session["user_id"] = user.id
    session["email"]   = email
    return jsonify({"email": email})


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@auth_bp.route("/api/me")
@login_required
def me():
    return jsonify({"email": session["email"], "user_id": session["user_id"]})
