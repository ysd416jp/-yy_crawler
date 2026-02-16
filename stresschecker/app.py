"""
ストレスチェックシステム - メインアプリケーション
厚生労働省「職業性ストレス簡易調査票（57項目）」準拠
"""

import os
import io
import csv
import json
import secrets
from datetime import datetime, date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, send_file, abort,
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import (
    db, SurveyPeriod, Department, Employee, AccessToken,
    Response, Result, AdminUser, generate_token,
)
from questions import QUESTIONS, CHOICE_SETS, GROUP_HEADERS, SUBSCALES, get_questions_by_group
from scoring import calculate_scores, get_result_comments, calculate_group_analysis

# =============================================================
# Flask App 設定
# =============================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///stresscheck.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    # 初期管理者がいなければ作成
    if not AdminUser.query.first():
        admin = AdminUser(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()

    # デモモード: 5名分のテストデータを自動作成
    if os.environ.get("DEMO_MODE") == "1" and not SurveyPeriod.query.first():
        depts = [
            Department(name="本社"),
            Department(name="A事業所"),
            Department(name="B事業所"),
        ]
        db.session.add_all(depts)
        db.session.flush()

        demo_employees = [
            ("田中太郎", depts[0].id),
            ("佐藤花子", depts[0].id),
            ("鈴木次郎", depts[1].id),
            ("高橋三郎", depts[1].id),
            ("伊藤四郎", depts[2].id),
        ]

        period = SurveyPeriod(
            name="2026年度 デモ実施",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            is_active=True,
        )
        db.session.add(period)
        db.session.flush()

        for i, (name, dept_id) in enumerate(demo_employees, 1):
            emp = Employee(name=name, department_id=dept_id, employee_code=f"E{i:03d}")
            db.session.add(emp)
            db.session.flush()
            tk = AccessToken(
                employee_id=emp.id,
                period_id=period.id,
                token=f"demo{i}",
            )
            db.session.add(tk)

        db.session.commit()


# =============================================================
# デコレータ
# =============================================================

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# =============================================================
# 受検者向けルート
# =============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/survey/<token>")
def survey_start(token):
    """トークンURLからアンケート開始"""
    tk = AccessToken.query.filter_by(token=token).first()
    if not tk:
        abort(404)

    # 既に回答済みの場合は結果表示へ
    if tk.is_completed:
        return redirect(url_for("survey_result", token=token))

    # 実施期間チェック
    period = tk.period
    if not period.is_ongoing:
        return render_template("survey/closed.html", period=period)

    # 開始日時を記録
    if not tk.started_at:
        tk.started_at = datetime.utcnow()
        db.session.commit()

    return render_template(
        "survey/start.html",
        token=tk,
        employee=tk.employee,
        period=period,
    )


@app.route("/survey/<token>/questions", methods=["GET", "POST"])
def survey_questions(token):
    """アンケート回答ページ"""
    tk = AccessToken.query.filter_by(token=token).first()
    if not tk:
        abort(404)
    if tk.is_completed:
        return redirect(url_for("survey_result", token=token))

    if request.method == "POST":
        # 全回答を保存
        answers = {}
        missing = []
        for q in QUESTIONS:
            key = f"q{q['number']}"
            val = request.form.get(key)
            if val is None:
                missing.append(q["number"])
            else:
                answers[q["number"]] = int(val)

        if missing:
            flash(f"未回答の質問があります（Q{', Q'.join(map(str, missing))}）", "error")
            return render_template(
                "survey/questionnaire.html",
                token=tk,
                questions=QUESTIONS,
                choice_sets=CHOICE_SETS,
                group_headers=GROUP_HEADERS,
                answers=answers,
            )

        # 回答をDBに保存
        for qnum, val in answers.items():
            resp = Response(
                token_id=tk.id,
                question_number=qnum,
                answer_value=val,
            )
            db.session.add(resp)

        # スコア計算
        scores = calculate_scores(answers)
        comments = get_result_comments(scores)

        result = Result(
            token_id=tk.id,
            employee_id=tk.employee_id,
            period_id=tk.period_id,
            scores_json=json.dumps(scores, ensure_ascii=False),
            is_high_stress=scores["is_high_stress"],
            stress_level=scores["stress_level"],
        )
        db.session.add(result)

        tk.is_completed = True
        tk.completed_at = datetime.utcnow()
        db.session.commit()

        return redirect(url_for("survey_result", token=token))

    return render_template(
        "survey/questionnaire.html",
        token=tk,
        questions=QUESTIONS,
        choice_sets=CHOICE_SETS,
        group_headers=GROUP_HEADERS,
        answers={},
    )


@app.route("/survey/<token>/result")
def survey_result(token):
    """個人結果表示"""
    tk = AccessToken.query.filter_by(token=token).first()
    if not tk or not tk.is_completed:
        abort(404)

    result = tk.result
    scores = json.loads(result.scores_json)
    comments = get_result_comments(scores)

    return render_template(
        "survey/result.html",
        token=tk,
        employee=tk.employee,
        scores=scores,
        comments=comments,
        subscales=SUBSCALES,
    )


# =============================================================
# 管理者向けルート
# =============================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = AdminUser.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["admin_id"] = user.id
            session["admin_username"] = user.username
            return redirect(url_for("admin_dashboard"))
        flash("ユーザー名またはパスワードが正しくありません", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    """管理者ダッシュボード"""
    periods = SurveyPeriod.query.order_by(SurveyPeriod.id.desc()).all()
    active_period = SurveyPeriod.query.filter_by(is_active=True).first()

    stats = {}
    if active_period:
        tokens = AccessToken.query.filter_by(period_id=active_period.id).all()
        completed = [t for t in tokens if t.is_completed]
        high_stress = Result.query.filter_by(
            period_id=active_period.id, is_high_stress=True
        ).count()

        stats = {
            "total": len(tokens),
            "completed": len(completed),
            "rate": round(len(completed) / len(tokens) * 100, 1) if tokens else 0,
            "high_stress": high_stress,
        }

    return render_template(
        "admin/dashboard.html",
        periods=periods,
        active_period=active_period,
        stats=stats,
    )


@app.route("/admin/periods", methods=["GET", "POST"])
@admin_required
def admin_periods():
    """実施期間管理"""
    if request.method == "POST":
        name = request.form.get("name")
        start = request.form.get("start_date")
        end = request.form.get("end_date")

        if name and start and end:
            period = SurveyPeriod(
                name=name,
                start_date=datetime.strptime(start, "%Y-%m-%d").date(),
                end_date=datetime.strptime(end, "%Y-%m-%d").date(),
            )
            db.session.add(period)
            db.session.commit()
            flash("実施期間を追加しました", "success")
        return redirect(url_for("admin_periods"))

    periods = SurveyPeriod.query.order_by(SurveyPeriod.id.desc()).all()
    return render_template("admin/periods.html", periods=periods)


@app.route("/admin/periods/<int:period_id>/toggle")
@admin_required
def toggle_period(period_id):
    period = SurveyPeriod.query.get_or_404(period_id)
    period.is_active = not period.is_active
    db.session.commit()
    return redirect(url_for("admin_periods"))


@app.route("/admin/departments", methods=["GET", "POST"])
@admin_required
def admin_departments():
    """部署管理"""
    if request.method == "POST":
        name = request.form.get("name")
        parent_id = request.form.get("parent_id") or None
        if name:
            dept = Department(name=name, parent_id=parent_id)
            db.session.add(dept)
            db.session.commit()
            flash("部署を追加しました", "success")
        return redirect(url_for("admin_departments"))

    departments = Department.query.all()
    return render_template("admin/departments.html", departments=departments)


@app.route("/admin/employees", methods=["GET", "POST"])
@admin_required
def admin_employees():
    """従業員管理"""
    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            name = request.form.get("name")
            dept_id = request.form.get("department_id") or None
            code = request.form.get("employee_code") or None
            if name:
                emp = Employee(name=name, department_id=dept_id, employee_code=code)
                db.session.add(emp)
                db.session.commit()
                flash("従業員を追加しました", "success")

        elif action == "csv_upload":
            file = request.files.get("csv_file")
            if file:
                count = _import_employees_csv(file)
                flash(f"{count}名の従業員を登録しました", "success")

        return redirect(url_for("admin_employees"))

    employees = Employee.query.order_by(Employee.department_id, Employee.name).all()
    departments = Department.query.all()
    return render_template(
        "admin/employees.html",
        employees=employees,
        departments=departments,
    )


def _import_employees_csv(file):
    """CSVから従業員を一括登録"""
    stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
    reader = csv.DictReader(stream)
    count = 0
    for row in reader:
        name = row.get("名前", row.get("name", "")).strip()
        if not name:
            continue
        dept_name = row.get("部署", row.get("department", "")).strip()
        code = row.get("社員番号", row.get("code", "")).strip() or None

        dept_id = None
        if dept_name:
            dept = Department.query.filter_by(name=dept_name).first()
            if not dept:
                dept = Department(name=dept_name)
                db.session.add(dept)
                db.session.flush()
            dept_id = dept.id

        emp = Employee(name=name, department_id=dept_id, employee_code=code)
        db.session.add(emp)
        count += 1

    db.session.commit()
    return count


@app.route("/admin/employees/<int:emp_id>/delete", methods=["POST"])
@admin_required
def delete_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    db.session.delete(emp)
    db.session.commit()
    flash("従業員を削除しました", "success")
    return redirect(url_for("admin_employees"))


@app.route("/admin/tokens")
@admin_required
def admin_tokens():
    """トークン管理"""
    period_id = request.args.get("period_id", type=int)
    periods = SurveyPeriod.query.order_by(SurveyPeriod.id.desc()).all()

    if not period_id and periods:
        period_id = periods[0].id

    tokens = []
    if period_id:
        tokens = (
            AccessToken.query
            .filter_by(period_id=period_id)
            .join(Employee)
            .order_by(Employee.name)
            .all()
        )

    return render_template(
        "admin/tokens.html",
        periods=periods,
        tokens=tokens,
        selected_period_id=period_id,
    )


@app.route("/admin/tokens/generate", methods=["POST"])
@admin_required
def generate_tokens():
    """全従業員にトークンを一括発行"""
    period_id = request.form.get("period_id", type=int)
    if not period_id:
        flash("実施期間を選択してください", "error")
        return redirect(url_for("admin_tokens"))

    employees = Employee.query.all()
    count = 0
    for emp in employees:
        existing = AccessToken.query.filter_by(
            employee_id=emp.id, period_id=period_id
        ).first()
        if not existing:
            tk = AccessToken(employee_id=emp.id, period_id=period_id)
            db.session.add(tk)
            count += 1

    db.session.commit()
    flash(f"{count}名分のトークンを発行しました", "success")
    return redirect(url_for("admin_tokens", period_id=period_id))


@app.route("/admin/tokens/pdf")
@admin_required
def tokens_pdf():
    """トークンURL+QRコード一覧のPDF出力"""
    period_id = request.args.get("period_id", type=int)
    if not period_id:
        abort(400)

    tokens = (
        AccessToken.query
        .filter_by(period_id=period_id)
        .join(Employee)
        .order_by(Employee.department_id, Employee.name)
        .all()
    )

    base_url = request.host_url.rstrip("/")

    try:
        from pdf_generator import generate_token_pdf
        pdf_bytes = generate_token_pdf(tokens, base_url)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"stresscheck_tokens_{period_id}.pdf",
        )
    except ImportError:
        # PDF生成ライブラリがない場合はCSV出力にフォールバック
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["名前", "部署", "URL", "トークン"])
        for tk in tokens:
            dept_name = tk.employee.department.name if tk.employee.department else ""
            url = f"{base_url}/survey/{tk.token}"
            writer.writerow([tk.employee.name, dept_name, url, tk.token])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8-sig")),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"stresscheck_tokens_{period_id}.csv",
        )


@app.route("/admin/analysis")
@admin_required
def admin_analysis():
    """集団分析"""
    period_id = request.args.get("period_id", type=int)
    dept_id = request.args.get("department_id", type=int)
    periods = SurveyPeriod.query.order_by(SurveyPeriod.id.desc()).all()
    departments = Department.query.all()

    if not period_id and periods:
        period_id = periods[0].id

    analysis = None
    dept_analyses = []

    if period_id:
        # 全体分析
        query = Result.query.filter_by(period_id=period_id)
        if dept_id:
            query = query.join(Employee).filter(Employee.department_id == dept_id)

        results = query.all()
        if results:
            all_scores = [json.loads(r.scores_json) for r in results]
            analysis = calculate_group_analysis(all_scores)

        # 部署別分析
        for dept in departments:
            dept_results = (
                Result.query
                .filter_by(period_id=period_id)
                .join(Employee)
                .filter(Employee.department_id == dept.id)
                .all()
            )
            if dept_results:
                dept_scores = [json.loads(r.scores_json) for r in dept_results]
                dept_analysis = calculate_group_analysis(dept_scores)
                dept_analyses.append({
                    "department": dept,
                    "analysis": dept_analysis,
                })

    return render_template(
        "admin/analysis.html",
        periods=periods,
        departments=departments,
        selected_period_id=period_id,
        selected_dept_id=dept_id,
        analysis=analysis,
        dept_analyses=dept_analyses,
        subscales=SUBSCALES,
    )


@app.route("/admin/results")
@admin_required
def admin_results():
    """個人結果一覧（実施事務従事者用）"""
    period_id = request.args.get("period_id", type=int)
    periods = SurveyPeriod.query.order_by(SurveyPeriod.id.desc()).all()

    if not period_id and periods:
        period_id = periods[0].id

    results = []
    if period_id:
        results = (
            Result.query
            .filter_by(period_id=period_id)
            .join(Employee)
            .order_by(Employee.department_id, Employee.name)
            .all()
        )

    return render_template(
        "admin/results.html",
        periods=periods,
        results=results,
        selected_period_id=period_id,
    )


@app.route("/admin/password", methods=["GET", "POST"])
@admin_required
def admin_password():
    """パスワード変更"""
    if request.method == "POST":
        current = request.form.get("current_password")
        new_pw = request.form.get("new_password")
        confirm = request.form.get("confirm_password")

        admin = AdminUser.query.get(session["admin_id"])
        if not check_password_hash(admin.password_hash, current):
            flash("現在のパスワードが正しくありません", "error")
        elif new_pw != confirm:
            flash("新しいパスワードが一致しません", "error")
        elif len(new_pw) < 8:
            flash("パスワードは8文字以上にしてください", "error")
        else:
            admin.password_hash = generate_password_hash(new_pw)
            db.session.commit()
            flash("パスワードを変更しました", "success")
            return redirect(url_for("admin_dashboard"))

    return render_template("admin/password.html")


# =============================================================
# API エンドポイント（チャート用データ）
# =============================================================

@app.route("/api/result/<token>/chart")
def api_result_chart(token):
    """個人結果のレーダーチャート用データ"""
    tk = AccessToken.query.filter_by(token=token).first()
    if not tk or not tk.is_completed:
        abort(404)

    scores = json.loads(tk.result.scores_json)

    # レーダーチャート用にA群・B群のスコアを整形
    labels = []
    values = []
    for key in ["workload_quantity", "workload_quality", "physical_demand",
                "interpersonal", "environment", "job_control",
                "skill_utilization", "job_fitness", "meaningfulness"]:
        labels.append(SUBSCALES[key]["name"])
        values.append(scores["subscale_scores"][key])

    return jsonify({
        "stressors": {"labels": labels, "values": values},
        "reactions": {
            "labels": [SUBSCALES[k]["name"] for k in
                       ["vitality", "irritability", "fatigue", "anxiety", "depression", "somatic"]],
            "values": [scores["subscale_scores"][k] for k in
                       ["vitality", "irritability", "fatigue", "anxiety", "depression", "somatic"]],
        },
        "support": {
            "labels": [SUBSCALES[k]["name"] for k in
                       ["supervisor_support", "coworker_support", "family_support"]],
            "values": [scores["subscale_scores"][k] for k in
                       ["supervisor_support", "coworker_support", "family_support"]],
        },
    })


# =============================================================
# エントリポイント
# =============================================================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
