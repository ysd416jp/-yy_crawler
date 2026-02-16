"""
データベースモデル定義（SQLite + SQLAlchemy）
"""

import os
import uuid
import secrets
from datetime import datetime, date

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def generate_token():
    """推測困難な一意トークンを生成（URLセーフ、32文字）"""
    return secrets.token_urlsafe(24)


class SurveyPeriod(db.Model):
    """実施期間"""
    __tablename__ = "survey_periods"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 例: "2026年度 第1回"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tokens = db.relationship("AccessToken", backref="period", lazy=True)

    @property
    def is_ongoing(self):
        today = date.today()
        return self.is_active and self.start_date <= today <= self.end_date

    @property
    def completion_rate(self):
        if not self.tokens:
            return 0
        completed = sum(1 for t in self.tokens if t.is_completed)
        return round(completed / len(self.tokens) * 100, 1)


class Department(db.Model):
    """部署・事業所"""
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    parent = db.relationship("Department", remote_side=[id], backref="children")
    employees = db.relationship("Employee", backref="department", lazy=True)


class Employee(db.Model):
    """従業員"""
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(50), nullable=True)  # 社員番号（任意）
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tokens = db.relationship("AccessToken", backref="employee", lazy=True)


class AccessToken(db.Model):
    """受検用アクセストークン（個人ごとに一意のURLを発行）"""
    __tablename__ = "access_tokens"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(50), unique=True, nullable=False, default=generate_token)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey("survey_periods.id"), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    responses = db.relationship("Response", backref="access_token", lazy=True)
    result = db.relationship("Result", backref="access_token", uselist=False)


class Response(db.Model):
    """個別の回答"""
    __tablename__ = "responses"

    id = db.Column(db.Integer, primary_key=True)
    token_id = db.Column(db.Integer, db.ForeignKey("access_tokens.id"), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    answer_value = db.Column(db.Integer, nullable=False)  # 1-4
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("token_id", "question_number", name="uq_token_question"),
    )


class Result(db.Model):
    """計算済み結果"""
    __tablename__ = "results"

    id = db.Column(db.Integer, primary_key=True)
    token_id = db.Column(db.Integer, db.ForeignKey("access_tokens.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey("survey_periods.id"), nullable=False)
    scores_json = db.Column(db.Text, nullable=False)  # JSON: calculate_scores() の結果
    is_high_stress = db.Column(db.Boolean, default=False)
    stress_level = db.Column(db.String(20), nullable=False)  # low / moderate / high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship("Employee", backref="results")


class AdminUser(db.Model):
    """管理者ユーザー"""
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="admin")  # admin / implementer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
