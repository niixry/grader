import csv
import io

from flask import Blueprint, Response, jsonify, request, session
from sqlalchemy.orm import joinedload

from decorators import login_required
from models import Group, Result, db

results_bp = Blueprint("results", __name__)


@results_bp.route("/results", methods=["GET"])
@login_required
def get_results():
    group_id = request.args.get("group_id", type=int)
    query = Result.query.options(joinedload(Result.group)).filter_by(user_id=session["user_id"])
    if group_id:
        query = query.filter(Result.group_id == group_id)
    records = query.order_by(Result.created_at.desc()).limit(200).all()
    return jsonify([{
        "id":           r.id,
        "student_name": r.student_name,
        "task":         r.task,
        "criteria":     r.criteria,
        "score":        r.score,
        "comment":      r.comment,
        "errors":       r.errors or [],
        "created_at":   r.created_at.isoformat() if r.created_at else "",
        "group_id":     r.group_id,
        "group_name":   r.group.name if r.group else None,
    } for r in records])


@results_bp.route("/results/<int:result_id>", methods=["DELETE"])
@login_required
def delete_result(result_id):
    record = Result.query.filter_by(id=result_id, user_id=session["user_id"]).first()
    if not record:
        return jsonify({"error": "Запись не найдена"}), 404

    try:
        db.session.delete(record)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500

    return jsonify({"success": True})


@results_bp.route("/export/csv", methods=["GET"])
@login_required
def export_csv():
    records = (
        Result.query
        .options(joinedload(Result.group))
        .filter_by(user_id=session["user_id"])
        .order_by(Result.created_at.desc())
        .all()
    )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Группа", "ФИ ученика", "Задание", "Критерии", "Оценка", "Ошибки", "Комментарий", "Дата"])
    for r in records:
        errors_str = ", ".join(r.errors or [])
        date_str   = r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else ""
        group_name = r.group.name if r.group else ""
        writer.writerow([group_name, r.student_name, r.task, r.criteria, r.score, errors_str, r.comment, date_str])

    csv_bytes = ("﻿" + buf.getvalue()).encode("utf-8")
    return Response(
        csv_bytes,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=results.csv",
            "Content-Length": len(csv_bytes),
        },
    )
