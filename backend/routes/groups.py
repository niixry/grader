from flask import Blueprint, jsonify, request, session

from decorators import login_required
from models import Group, db

groups_bp = Blueprint("groups", __name__)


@groups_bp.route("/groups", methods=["GET"])
@login_required
def list_groups():
    groups = (
        Group.query
        .filter_by(user_id=session["user_id"])
        .order_by(Group.created_at.desc())
        .all()
    )
    return jsonify([{"id": g.id, "name": g.name, "description": g.description} for g in groups])


@groups_bp.route("/groups", methods=["POST"])
@login_required
def create_group():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Введите название группы"}), 400
    group = Group(
        name=name,
        description=(data.get("description") or "").strip() or None,
        user_id=session["user_id"],
    )
    db.session.add(group)
    db.session.commit()
    return jsonify({"id": group.id, "name": group.name, "description": group.description}), 201


@groups_bp.route("/groups/<int:group_id>", methods=["DELETE"])
@login_required
def delete_group(group_id):
    group = Group.query.filter_by(id=group_id, user_id=session["user_id"]).first()
    if not group:
        return jsonify({"error": "Группа не найдена"}), 404
    db.session.delete(group)
    db.session.commit()
    return jsonify({"success": True})
