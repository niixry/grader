from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    results = db.relationship("Result", backref="user", lazy=True, cascade="all, delete-orphan")
    groups  = db.relationship("Group", back_populates="user", lazy=True, cascade="all, delete-orphan")


class Group(db.Model):
    __tablename__ = "groups"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at  = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user    = db.relationship("User", back_populates="groups", lazy=True)
    results = db.relationship("Result", back_populates="group", lazy=True)


class Result(db.Model):
    __tablename__ = "results"
    __table_args__ = (
        Index("idx_results_user_id", "user_id"),
        Index("idx_results_created_at", "created_at"),
    )

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id     = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="SET NULL"), nullable=True, index=True)
    student_name = db.Column(db.String(255), nullable=False, default="")
    task         = db.Column(db.Text, nullable=False)
    criteria     = db.Column(db.Text, nullable=False)
    score        = db.Column(db.SmallInteger, nullable=False)
    comment      = db.Column(db.Text, nullable=False)
    errors       = db.Column(db.JSON, nullable=False, default=list)
    created_at   = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    group = db.relationship("Group", back_populates="results", lazy=True)
