"""デモデータ投入スクリプト"""
from datetime import date, datetime
from app import app
from models import db, SurveyPeriod, Department, Employee, AccessToken, AdminUser

with app.app_context():
    db.create_all()

    # 既にデモデータがあればスキップ
    if SurveyPeriod.query.first():
        print("Demo data already exists.")
        # トークン一覧を表示
        tokens = AccessToken.query.all()
        for tk in tokens:
            print(f"  {tk.employee.name}: /survey/{tk.token}")
        exit()

    # 部署
    dept1 = Department(name="本社")
    dept2 = Department(name="A事業所")
    dept3 = Department(name="B事業所")
    db.session.add_all([dept1, dept2, dept3])
    db.session.flush()

    # 従業員（デモ用5名）
    employees = [
        Employee(name="テスト太郎", department_id=dept1.id, employee_code="D001"),
        Employee(name="テスト花子", department_id=dept1.id, employee_code="D002"),
        Employee(name="テスト次郎", department_id=dept2.id, employee_code="D003"),
        Employee(name="テスト三郎", department_id=dept2.id, employee_code="D004"),
        Employee(name="テスト四郎", department_id=dept3.id, employee_code="D005"),
    ]
    db.session.add_all(employees)
    db.session.flush()

    # 実施期間（今日を含む）
    period = SurveyPeriod(
        name="2026年度 デモ実施",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 3, 31),
        is_active=True,
    )
    db.session.add(period)
    db.session.flush()

    # トークン発行
    for emp in employees:
        tk = AccessToken(employee_id=emp.id, period_id=period.id)
        db.session.add(tk)

    db.session.commit()

    # 結果表示
    print("Demo data created!")
    print(f"Admin: admin / admin123")
    print(f"Survey period: {period.name}")
    print(f"\nAccess URLs:")
    tokens = AccessToken.query.all()
    for tk in tokens:
        print(f"  {tk.employee.name}: /survey/{tk.token}")
