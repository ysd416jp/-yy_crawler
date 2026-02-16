"""
架空従業員データベース（145名）
医療法人を想定した5事業所・17部署

集団分析の観点:
  - 10人以上の部署（集団分析可能）: 8部署
  - 10人未満の部署（要集約）      : 9部署
  → 現実的な混在パターンを再現

事業所構成:
  - クリニック1          (34名, 4部署: 12/10/6/6)
  - クリニック2          (33名, 4部署: 11/10/6/6)
  - 訪問看護ステーション1 (29名, 3部署: 12/10/7)
  - 訪問看護ステーション2 (29名, 3部署: 12/10/7)
  - 医療法人本部         (20名, 3部署: 7/6/7)
"""

from datetime import date

from models import db, Department, Employee, SurveyPeriod, AccessToken

# =============================================================
# 従業員データ (145名)
# 各タプル: (氏名, 生年月日, 入職日, 管理職フラグ)
#
# ★ = 10人以上（集団分析OK）
# ☆ = 10人未満（事業所単位で集約が必要）
# =============================================================

# --- クリニック1 (34名) ---
CLINIC1_EMPLOYEES = {
    "外来看護": [  # ★12名
        ("山田 真由美", date(1975, 3, 15), date(2002, 4, 1), True),
        ("鈴木 恵子",   date(1982, 7, 22), date(2008, 4, 1), False),
        ("佐藤 陽子",   date(1988, 11, 3), date(2012, 4, 1), False),
        ("高橋 美咲",   date(1990, 5, 18), date(2014, 4, 1), False),
        ("渡辺 千尋",   date(1993, 1, 7),  date(2016, 4, 1), False),
        ("伊藤 沙織",   date(1996, 8, 25), date(2020, 4, 1), False),
        ("中村 結衣",   date(1999, 12, 10), date(2023, 4, 1), False),
        ("川上 美穂",   date(1986, 4, 17), date(2010, 4, 1), False),
        ("土屋 紗希",   date(1991, 9, 2),  date(2015, 4, 1), False),
        ("松岡 遥",     date(1994, 2, 20), date(2018, 4, 1), False),
        ("水野 愛",     date(1997, 6, 8),  date(2021, 4, 1), False),
        ("白石 菜々子", date(2001, 3, 28), date(2025, 4, 1), False),
    ],
    "リハビリテーション": [  # ★10名
        ("小林 健一",   date(1978, 6, 8),  date(2004, 4, 1), True),
        ("加藤 大輔",   date(1985, 2, 14), date(2009, 4, 1), False),
        ("吉田 裕也",   date(1989, 9, 20), date(2013, 4, 1), False),
        ("松本 翔太",   date(1992, 4, 5),  date(2016, 4, 1), False),
        ("井上 麻衣",   date(1995, 10, 30), date(2019, 4, 1), False),
        ("木村 春香",   date(1998, 3, 12), date(2022, 4, 1), False),
        ("堀 康平",     date(1987, 7, 25), date(2011, 4, 1), False),
        ("市川 祐介",   date(1993, 12, 6), date(2017, 4, 1), False),
        ("浅野 真希",   date(1996, 5, 19), date(2020, 4, 1), False),
        ("谷口 拓也",   date(2000, 8, 14), date(2024, 4, 1), False),
    ],
    "医療事務": [  # ☆6名
        ("林 和子",     date(1972, 8, 19), date(2000, 4, 1), True),
        ("斎藤 典子",   date(1984, 12, 1), date(2007, 4, 1), False),
        ("清水 美香",   date(1987, 6, 28), date(2011, 4, 1), False),
        ("山崎 彩",     date(1991, 3, 16), date(2015, 4, 1), False),
        ("森 奈々",     date(1994, 7, 9),  date(2018, 4, 1), False),
        ("池田 葉月",   date(2000, 11, 23), date(2024, 4, 1), False),
    ],
    "検査・放射線": [  # ☆6名
        ("橋本 誠",     date(1976, 1, 25), date(2003, 4, 1), True),
        ("阿部 雄二",   date(1983, 5, 11), date(2008, 10, 1), False),
        ("石川 直樹",   date(1988, 10, 7), date(2013, 4, 1), False),
        ("前田 瞳",     date(1992, 2, 28), date(2016, 4, 1), False),
        ("藤田 康平",   date(1995, 9, 14), date(2019, 4, 1), False),
        ("小川 美月",   date(1999, 4, 3),  date(2023, 4, 1), False),
    ],
}

# --- クリニック2 (33名) ---
CLINIC2_EMPLOYEES = {
    "外来看護": [  # ★11名
        ("岡田 裕子",   date(1974, 11, 5), date(2001, 4, 1), True),
        ("後藤 智子",   date(1981, 3, 30), date(2006, 4, 1), False),
        ("長谷川 綾",   date(1986, 8, 17), date(2010, 4, 1), False),
        ("村上 里美",   date(1990, 1, 22), date(2014, 4, 1), False),
        ("近藤 詩織",   date(1993, 6, 9),  date(2017, 4, 1), False),
        ("石井 遥",     date(1997, 12, 4), date(2021, 4, 1), False),
        ("坂本 菜々子", date(2000, 5, 19), date(2024, 4, 1), False),
        ("吉川 理恵",   date(1985, 10, 11), date(2009, 4, 1), False),
        ("奥村 由美",   date(1992, 3, 26), date(2016, 4, 1), False),
        ("桜井 沙織",   date(1998, 7, 5),  date(2022, 4, 1), False),
        ("富田 瞳",     date(2002, 1, 18), date(2025, 4, 1), False),
    ],
    "リハビリテーション": [  # ★10名
        ("遠藤 隆",     date(1977, 4, 12), date(2003, 4, 1), True),
        ("青木 拓也",   date(1984, 9, 27), date(2009, 4, 1), False),
        ("藤井 達也",   date(1989, 2, 8),  date(2013, 4, 1), False),
        ("西村 慎一",   date(1991, 7, 15), date(2015, 10, 1), False),
        ("福田 真希",   date(1994, 11, 20), date(2018, 4, 1), False),
        ("太田 祐介",   date(1998, 6, 1),  date(2022, 4, 1), False),
        ("栗原 健太",   date(1986, 1, 30), date(2010, 4, 1), False),
        ("矢野 雅也",   date(1993, 8, 15), date(2017, 4, 1), False),
        ("五十嵐 学",   date(1997, 4, 22), date(2021, 4, 1), False),
        ("菅原 翔太",   date(2001, 10, 9), date(2025, 4, 1), False),
    ],
    "医療事務": [  # ☆6名
        ("三浦 幸子",   date(1973, 9, 8),  date(2001, 4, 1), True),
        ("岡本 明美",   date(1983, 1, 14), date(2007, 4, 1), False),
        ("松田 優子",   date(1988, 5, 26), date(2012, 4, 1), False),
        ("中島 友美",   date(1991, 10, 3), date(2015, 4, 1), False),
        ("中野 早紀",   date(1995, 3, 18), date(2019, 4, 1), False),
        ("原田 千夏",   date(2001, 8, 7),  date(2025, 4, 1), False),
    ],
    "検査・放射線": [  # ☆6名
        ("小野 浩",     date(1975, 12, 20), date(2002, 4, 1), True),
        ("田村 正人",   date(1982, 4, 6),  date(2007, 10, 1), False),
        ("竹内 亮",     date(1987, 7, 23), date(2012, 4, 1), False),
        ("金子 香織",   date(1992, 11, 11), date(2016, 4, 1), False),
        ("和田 光",     date(1996, 2, 15), date(2020, 4, 1), False),
        ("中山 桃子",   date(2000, 9, 28), date(2024, 4, 1), False),
    ],
}

# --- 訪問看護ステーション1 (29名) ---
VISITING1_EMPLOYEES = {
    "訪問看護": [  # ★12名
        ("石田 京子",   date(1971, 5, 3),  date(1999, 4, 1), True),
        ("上田 直美",   date(1979, 10, 18), date(2005, 4, 1), False),
        ("森田 久美子", date(1983, 2, 7),  date(2008, 4, 1), False),
        ("原 理恵",     date(1986, 6, 25), date(2010, 4, 1), False),
        ("柴田 美紀",   date(1989, 12, 14), date(2013, 4, 1), False),
        ("酒井 舞",     date(1992, 4, 30), date(2016, 4, 1), False),
        ("工藤 志保",   date(1994, 8, 8),  date(2018, 4, 1), False),
        ("横山 愛",     date(1997, 1, 22), date(2020, 4, 1), False),
        ("宮崎 紗希",   date(1999, 6, 16), date(2023, 4, 1), False),
        ("安藤 美穂",   date(2001, 11, 9), date(2025, 4, 1), False),
        ("東 裕子",     date(1988, 3, 14), date(2012, 4, 1), False),
        ("尾崎 恵子",   date(1995, 7, 28), date(2019, 4, 1), False),
    ],
    "訪問リハビリ": [  # ★10名
        ("内田 修",     date(1976, 7, 13), date(2002, 4, 1), True),
        ("大野 将",     date(1984, 3, 28), date(2009, 4, 1), False),
        ("杉山 圭",     date(1988, 8, 5),  date(2012, 4, 1), False),
        ("丸山 悟",     date(1991, 12, 19), date(2015, 4, 1), False),
        ("今井 聡",     date(1994, 5, 4),  date(2018, 4, 1), False),
        ("河野 恵介",   date(1997, 10, 21), date(2021, 4, 1), False),
        ("藤原 学",     date(2000, 3, 7),  date(2024, 4, 1), False),
        ("平野 淳",     date(2002, 7, 30), date(2025, 4, 1), False),
        ("辻 達也",     date(1990, 1, 16), date(2014, 4, 1), False),
        ("長田 康平",   date(1998, 11, 3), date(2022, 4, 1), False),
    ],
    "相談・調整": [  # ☆7名
        ("野口 洋子",   date(1973, 4, 20), date(2000, 4, 1), True),
        ("松井 悦子",   date(1981, 9, 6),  date(2006, 4, 1), False),
        ("田口 亜美",   date(1986, 1, 31), date(2010, 4, 1), False),
        ("高木 真理子", date(1990, 7, 12), date(2014, 4, 1), False),
        ("千葉 知恵",   date(1993, 11, 27), date(2017, 4, 1), False),
        ("岩田 美咲",   date(1996, 5, 15), date(2020, 4, 1), False),
        ("望月 紗希",   date(2000, 2, 3),  date(2024, 4, 1), False),
    ],
}

# --- 訪問看護ステーション2 (29名) ---
VISITING2_EMPLOYEES = {
    "訪問看護": [  # ★12名
        ("久保 恵子",   date(1970, 8, 14), date(1998, 4, 1), True),
        ("山口 陽子",   date(1980, 3, 2),  date(2005, 4, 1), False),
        ("佐々木 裕子", date(1984, 7, 19), date(2009, 4, 1), False),
        ("島田 真由美", date(1987, 11, 8), date(2011, 4, 1), False),
        ("川崎 花子",   date(1990, 5, 24), date(2014, 4, 1), False),
        ("中田 千尋",   date(1993, 10, 1), date(2017, 4, 1), False),
        ("本田 綾",     date(1995, 2, 17), date(2019, 4, 1), False),
        ("大塚 沙織",   date(1998, 6, 30), date(2022, 4, 1), False),
        ("片山 結衣",   date(2000, 12, 5), date(2024, 4, 1), False),
        ("北村 麻衣",   date(2002, 4, 18), date(2025, 4, 1), False),
        ("成田 直美",   date(1987, 5, 9),  date(2011, 4, 1), False),
        ("早川 千尋",   date(1996, 9, 22), date(2020, 4, 1), False),
    ],
    "訪問リハビリ": [  # ★10名
        ("須藤 武",     date(1977, 9, 10), date(2003, 4, 1), True),
        ("関口 健太",   date(1985, 1, 26), date(2009, 4, 1), False),
        ("宮本 雅也",   date(1989, 6, 13), date(2013, 4, 1), False),
        ("新井 哲也",   date(1992, 10, 29), date(2016, 4, 1), False),
        ("黒田 崇",     date(1995, 4, 7),  date(2019, 4, 1), False),
        ("小島 徹",     date(1998, 8, 22), date(2022, 4, 1), False),
        ("永井 秀樹",   date(2001, 1, 11), date(2024, 4, 1), False),
        ("荒木 真一",   date(2003, 5, 25), date(2025, 4, 1), False),
        ("星野 圭",     date(1990, 6, 18), date(2014, 4, 1), False),
        ("福井 祐介",   date(1999, 2, 4),  date(2023, 4, 1), False),
    ],
    "相談・調整": [  # ☆7名
        ("広瀬 和子",   date(1974, 12, 23), date(2001, 4, 1), True),
        ("川口 典子",   date(1982, 5, 9),  date(2007, 4, 1), False),
        ("飯田 美香",   date(1987, 9, 16), date(2011, 4, 1), False),
        ("古川 由美",   date(1991, 3, 4),  date(2015, 4, 1), False),
        ("大石 里美",   date(1994, 7, 21), date(2018, 4, 1), False),
        ("武田 春香",   date(1997, 12, 10), date(2021, 4, 1), False),
        ("野村 瞳",     date(2001, 6, 6),  date(2025, 4, 1), False),
    ],
}

# --- 医療法人本部 (20名) ---
HQ_EMPLOYEES = {
    "総務・人事": [  # ☆7名
        ("田中 豊",     date(1968, 3, 10), date(1996, 4, 1), True),
        ("佐藤 進",     date(1980, 8, 24), date(2005, 4, 1), False),
        ("鈴木 美穂",   date(1985, 1, 5),  date(2009, 4, 1), False),
        ("高橋 実",     date(1988, 6, 18), date(2012, 4, 1), False),
        ("渡辺 章",     date(1992, 11, 30), date(2016, 4, 1), False),
        ("伊藤 博",     date(1996, 4, 14), date(2020, 4, 1), False),
        ("中村 勇",     date(2000, 9, 1),  date(2024, 4, 1), False),
    ],
    "経理・財務": [  # ☆6名
        ("小林 洋",     date(1969, 7, 28), date(1997, 4, 1), True),
        ("加藤 幸一",   date(1981, 12, 13), date(2006, 4, 1), False),
        ("吉田 英二",   date(1986, 5, 2),  date(2010, 4, 1), False),
        ("松本 明",     date(1990, 10, 16), date(2014, 4, 1), False),
        ("井上 剛",     date(1993, 3, 25), date(2017, 4, 1), False),
        ("木村 正三",   date(1997, 8, 9),  date(2021, 4, 1), False),
    ],
    "企画・広報": [  # ☆7名
        ("林 和夫",     date(1970, 2, 15), date(1998, 4, 1), True),
        ("斎藤 雅也",   date(1982, 7, 7),  date(2007, 4, 1), False),
        ("清水 彩",     date(1987, 11, 22), date(2011, 4, 1), False),
        ("山崎 友美",   date(1991, 4, 8),  date(2015, 4, 1), False),
        ("森 達也",     date(1994, 9, 19), date(2018, 4, 1), False),
        ("池田 舞",     date(1998, 2, 28), date(2022, 4, 1), False),
        ("橋本 千夏",   date(2001, 7, 14), date(2025, 4, 1), False),
    ],
}

# 事業所→部署→従業員のマッピング
ALL_EMPLOYEE_DATA = [
    ("クリニック1", CLINIC1_EMPLOYEES),
    ("クリニック2", CLINIC2_EMPLOYEES),
    ("訪問看護ステーション1", VISITING1_EMPLOYEES),
    ("訪問看護ステーション2", VISITING2_EMPLOYEES),
    ("医療法人本部", HQ_EMPLOYEES),
]

# 社員コードプレフィックス
CODE_PREFIX = {
    "クリニック1": "C1",
    "クリニック2": "C2",
    "訪問看護ステーション1": "N1",
    "訪問看護ステーション2": "N2",
    "医療法人本部": "HQ",
}


def seed_employees():
    """
    145名分の従業員データと事業所・部署を一括登録する。
    すでにデータが存在する場合はスキップ。

    Returns:
        tuple: (作成した従業員リスト, SurveyPeriod)
    """
    if Employee.query.first():
        return [], None

    employees = []
    global_idx = 0

    for wp_name, dept_employees in ALL_EMPLOYEE_DATA:
        # 事業所（親部署）を作成
        workplace = Department(name=wp_name, parent_id=None)
        db.session.add(workplace)
        db.session.flush()

        prefix = CODE_PREFIX[wp_name]
        wp_idx = 0

        for dept_name, members in dept_employees.items():
            # 部署（子）を作成
            dept = Department(name=dept_name, parent_id=workplace.id)
            db.session.add(dept)
            db.session.flush()

            for name, birth, hire, is_mgr in members:
                wp_idx += 1
                global_idx += 1
                emp = Employee(
                    employee_code=f"{prefix}-{wp_idx:03d}",
                    name=name,
                    department_id=dept.id,
                    birth_date=birth,
                    hire_date=hire,
                    is_manager=is_mgr,
                )
                db.session.add(emp)
                employees.append(emp)

    db.session.flush()

    # 実施期間を作成
    period = SurveyPeriod(
        name="2026年度 第1回ストレスチェック",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        is_active=True,
    )
    db.session.add(period)
    db.session.flush()

    # 全従業員にアクセストークンを発行
    for emp in employees:
        tk = AccessToken(
            employee_id=emp.id,
            period_id=period.id,
        )
        db.session.add(tk)

    db.session.commit()
    return employees, period
