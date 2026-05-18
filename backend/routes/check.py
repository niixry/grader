import base64
import io
import os
import zipfile

from flask import Blueprint, jsonify, request, session

from decorators import login_required
from models import Group, Result, db
from utils import analyze_with_ai

check_bp = Blueprint("check", __name__)

_ZIP_TYPES = {"application/zip", "application/x-zip-compressed", "multipart/x-zip"}
_MAX_IMAGES = 10
_MAX_BYTES  = 5 * 1024 * 1024


def _images_from_single(file):
    if file.content_type not in ("image/jpeg", "image/png"):
        raise ValueError("Поддерживаются только JPG, PNG или ZIP-архив")
    data = file.read()
    if len(data) > _MAX_BYTES:
        raise ValueError("Размер файла превышает 5 МБ")
    return [(base64.b64encode(data).decode(), file.content_type)]


def _images_from_zip(data):
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = sorted(
            n for n in zf.namelist()
            if not n.startswith("__MACOSX") and os.path.splitext(n.lower())[1] in (".jpg", ".jpeg", ".png")
        )
        if not names:
            raise ValueError("В архиве нет изображений JPG/PNG")
        if len(names) > _MAX_IMAGES:
            raise ValueError(f"В архиве слишком много фото - максимум {_MAX_IMAGES}")
        images = []
        for name in names:
            img_data = zf.read(name)
            ext = os.path.splitext(name.lower())[1]
            ct = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
            images.append((base64.b64encode(img_data).decode(), ct))
    return images


@check_bp.route("/check", methods=["POST"])
@login_required
def check():
    user_id      = session["user_id"]
    student_name = request.form.get("student_name", "").strip()
    task         = request.form.get("task", "").strip()
    criteria     = request.form.get("criteria", "").strip()
    save         = request.form.get("save", "false").lower() == "true"
    group_id     = request.form.get("group_id", type=int)
    image_file   = request.files.get("image")

    if not task:
        return jsonify({"error": "Введите текст задания"}), 400
    if not criteria:
        return jsonify({"error": "Введите критерии оценивания"}), 400
    if not image_file:
        return jsonify({"error": "Загрузите фотографию или ZIP-архив"}), 400

    if group_id is not None:
        owns_group = Group.query.filter_by(id=group_id, user_id=user_id).first()
        if not owns_group:
            return jsonify({"error": "Группа не найдена"}), 400

    try:
        ct = image_file.content_type or ""
        if ct in _ZIP_TYPES or image_file.filename.lower().endswith(".zip"):
            raw = image_file.read()
            if len(raw) > _MAX_BYTES * _MAX_IMAGES:
                return jsonify({"error": "Архив слишком большой"}), 400
            images = _images_from_zip(raw)
        else:
            images = _images_from_single(image_file)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        result = analyze_with_ai(task, criteria, images)
    except Exception as exc:
        return jsonify({"error": f"Ошибка анализа: {exc}"}), 502

    result.setdefault("errors", [])
    result.setdefault("comment", "")
    result["saved"] = False

    if save and student_name:
        try:
            record = Result(
                user_id=user_id,
                group_id=group_id,
                student_name=student_name,
                task=task,
                criteria=criteria,
                score=result["score"],
                comment=result["comment"],
                errors=result["errors"],
            )
            db.session.add(record)
            db.session.commit()
            result["saved"] = True
        except Exception as exc:
            db.session.rollback()
            print("Ошибка сохранения в БД:", exc)

    return jsonify(result)
