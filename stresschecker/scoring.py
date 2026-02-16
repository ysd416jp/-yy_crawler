"""
ストレスチェック スコア計算・高ストレス者判定エンジン
厚生労働省「職業性ストレス簡易調査票」準拠

判定方法:
  - 素点換算方式（推奨）を使用
  - 各尺度の素点合計を5段階（1-5）に換算
  - 5が最もストレスが高い状態
"""

from questions import SUBSCALES, QUESTIONS

# =============================================================
# 素点換算テーブル
# キー: (項目数, reverse)
# 値: [(素点範囲min, 素点範囲max, 換算値), ...]
# reverse=True の尺度は高得点=良好 → 換算時に反転
# =============================================================

# 3項目尺度の換算テーブル（通常方向: 高得点=高ストレス）
CONV_3_REGULAR = [
    (3, 3, 1),
    (4, 5, 2),
    (6, 7, 3),
    (8, 9, 4),
    (10, 12, 5),
]

# 3項目尺度の換算テーブル（逆転方向: 高得点=低ストレス）
CONV_3_REVERSE = [
    (3, 3, 5),
    (4, 5, 4),
    (6, 7, 3),
    (8, 9, 2),
    (10, 12, 1),
]

# 1項目尺度の換算テーブル（通常方向）
CONV_1_REGULAR = [
    (1, 1, 1),
    (2, 2, 2),
    (3, 3, 4),
    (4, 4, 5),
]

# 1項目尺度の換算テーブル（逆転方向）
CONV_1_REVERSE = [
    (1, 1, 5),
    (2, 2, 4),
    (3, 3, 2),
    (4, 4, 1),
]

# 6項目尺度の換算テーブル（通常方向: 抑うつ感）
CONV_6_REGULAR = [
    (6, 6, 1),
    (7, 9, 2),
    (10, 14, 3),
    (15, 18, 4),
    (19, 24, 5),
]

# 11項目尺度の換算テーブル（通常方向: 身体愁訴）
CONV_11_REGULAR = [
    (11, 11, 1),
    (12, 16, 2),
    (17, 22, 3),
    (23, 29, 4),
    (30, 44, 5),
]


def _get_conversion_table(item_count, reverse):
    """項目数と逆転フラグから適切な換算テーブルを返す"""
    if item_count == 1:
        return CONV_1_REVERSE if reverse else CONV_1_REGULAR
    elif item_count == 3:
        return CONV_3_REVERSE if reverse else CONV_3_REGULAR
    elif item_count == 6:
        return CONV_6_REGULAR  # 抑うつ感のみ（通常方向のみ）
    elif item_count == 11:
        return CONV_11_REGULAR  # 身体愁訴のみ（通常方向のみ）
    else:
        raise ValueError(f"未対応の項目数: {item_count}")


def _convert_score(raw_sum, table):
    """素点合計を換算値に変換"""
    for min_val, max_val, converted in table:
        if min_val <= raw_sum <= max_val:
            return converted
    raise ValueError(f"素点 {raw_sum} が換算テーブルの範囲外です")


def calculate_scores(answers):
    """
    全回答から各尺度のスコアを計算する

    Args:
        answers: dict {質問番号(int): 回答値(int 1-4)}

    Returns:
        dict with:
            - subscale_scores: 各尺度の換算スコア(1-5)
            - subscale_raw: 各尺度の素点合計
            - group_scores: 群ごとの換算スコア合計
            - group_raw: 群ごとの素点合計
            - is_high_stress: 高ストレス判定結果
            - stress_level: ストレスレベル ("low", "moderate", "high")
            - profile: ストレスプロフィール詳細
    """
    subscale_scores = {}
    subscale_raw = {}

    for key, scale in SUBSCALES.items():
        # 素点合計を計算
        raw_sum = sum(answers.get(q, 0) for q in scale["items"])
        subscale_raw[key] = raw_sum

        # 換算テーブルを取得して変換
        table = _get_conversion_table(len(scale["items"]), scale["reverse"])
        subscale_scores[key] = _convert_score(raw_sum, table)

    # 群ごとの合計
    group_scores = {"A": 0, "B": 0, "C": 0, "D": 0}
    group_raw = {"A": 0, "B": 0, "C": 0, "D": 0}

    for key, scale in SUBSCALES.items():
        group_scores[scale["group"]] += subscale_scores[key]
        group_raw[scale["group"]] += subscale_raw[key]

    # 高ストレス判定（素点換算方式）
    is_high_stress, stress_level = _judge_high_stress(group_scores)

    # ストレスプロフィール
    profile = _build_profile(subscale_scores, group_scores)

    return {
        "subscale_scores": subscale_scores,
        "subscale_raw": subscale_raw,
        "group_scores": group_scores,
        "group_raw": group_raw,
        "is_high_stress": is_high_stress,
        "stress_level": stress_level,
        "profile": profile,
    }


def _judge_high_stress(group_scores):
    """
    高ストレス者判定（素点換算方式）

    判定基準:
      条件1: B群合計 ≥ 17 → 高ストレス
      条件2: A群合計 + C群合計 ≥ 26 かつ B群合計 ≥ 12 → 高ストレス

    B群の範囲: 6尺度 × 1-5 = 6-30
    A群の範囲: 9尺度 × 1-5 = 9-45
    C群の範囲: 3尺度 × 1-5 = 3-15
    """
    b_total = group_scores["B"]
    a_total = group_scores["A"]
    c_total = group_scores["C"]

    # 条件1: ストレス反応が顕著に高い
    if b_total >= 17:
        return True, "high"

    # 条件2: ストレス要因+サポート不足が高く、かつ反応もやや高い
    if (a_total + c_total) >= 26 and b_total >= 12:
        return True, "high"

    # 中程度の判定
    if b_total >= 12 or (a_total + c_total) >= 22:
        return False, "moderate"

    return False, "low"


def _build_profile(subscale_scores, group_scores):
    """ストレスプロフィールを構築"""
    profile = {
        "stressors": {},
        "reactions": {},
        "support": {},
        "satisfaction": {},
    }

    for key, scale in SUBSCALES.items():
        score = subscale_scores[key]
        entry = {
            "name": scale["name"],
            "score": score,
            "level": _score_to_level(score),
        }

        if scale["group"] == "A":
            profile["stressors"][key] = entry
        elif scale["group"] == "B":
            profile["reactions"][key] = entry
        elif scale["group"] == "C":
            profile["support"][key] = entry
        elif scale["group"] == "D":
            profile["satisfaction"][key] = entry

    return profile


def _score_to_level(score):
    """換算スコアをレベル文字列に変換"""
    if score <= 1:
        return "very_low"
    elif score <= 2:
        return "low"
    elif score <= 3:
        return "moderate"
    elif score <= 4:
        return "high"
    else:
        return "very_high"


# =============================================================
# 集団分析用: 仕事のストレス判定図の計算
# =============================================================

# 全国平均値（職業性ストレス簡易調査票マニュアルより）
NATIONAL_AVERAGES = {
    "workload_quantity": {"mean": 7.6, "sd": 2.1},  # 量的負担
    "job_control": {"mean": 7.4, "sd": 2.1},  # コントロール
    "supervisor_support": {"mean": 7.5, "sd": 2.4},  # 上司支援
    "coworker_support": {"mean": 7.9, "sd": 2.1},  # 同僚支援
}


def calculate_group_analysis(all_results):
    """
    集団分析（仕事のストレス判定図）を計算する

    Args:
        all_results: list of calculate_scores() の結果

    Returns:
        dict with:
            - demand_control: 量-コントロール判定図データ
            - support: 職場の支援判定図データ
            - total_risk: 総合健康リスク
            - summary: 集団の要約統計
    """
    if not all_results:
        return None

    n = len(all_results)

    # 各尺度の素点平均を算出
    avg_workload = sum(r["subscale_raw"]["workload_quantity"] for r in all_results) / n
    avg_control = sum(r["subscale_raw"]["job_control"] for r in all_results) / n
    avg_supervisor = sum(r["subscale_raw"]["supervisor_support"] for r in all_results) / n
    avg_coworker = sum(r["subscale_raw"]["coworker_support"] for r in all_results) / n

    # 健康リスク計算（全国平均=100として標準化）
    # 量-コントロール判定図のリスク
    demand_risk = _calc_demand_control_risk(avg_workload, avg_control)

    # 職場の支援判定図のリスク
    support_risk = _calc_support_risk(avg_supervisor, avg_coworker)

    # 総合健康リスク
    total_risk = round(demand_risk * support_risk / 100)

    # 高ストレス者の割合
    high_stress_count = sum(1 for r in all_results if r["is_high_stress"])
    high_stress_rate = round(high_stress_count / n * 100, 1)

    # 各尺度のスコア分布
    summary = {
        "total_count": n,
        "high_stress_count": high_stress_count,
        "high_stress_rate": high_stress_rate,
        "avg_scores": {},
    }

    for key in SUBSCALES:
        scores = [r["subscale_scores"][key] for r in all_results]
        summary["avg_scores"][key] = {
            "name": SUBSCALES[key]["name"],
            "mean": round(sum(scores) / n, 2),
        }

    return {
        "demand_control": {
            "workload": round(avg_workload, 1),
            "control": round(avg_control, 1),
            "risk": demand_risk,
        },
        "support": {
            "supervisor": round(avg_supervisor, 1),
            "coworker": round(avg_coworker, 1),
            "risk": support_risk,
        },
        "total_risk": total_risk,
        "summary": summary,
    }


def _calc_demand_control_risk(workload, control):
    """量-コントロール判定図から健康リスクを算出"""
    nat_wl = NATIONAL_AVERAGES["workload_quantity"]
    nat_ct = NATIONAL_AVERAGES["job_control"]

    # 標準化スコア（全国平均からの偏差）
    wl_z = (workload - nat_wl["mean"]) / nat_wl["sd"]
    ct_z = (control - nat_ct["mean"]) / nat_ct["sd"]

    # リスク = 需要が高く、コントロールが低いほど高い
    # 100を基準として計算
    risk = 100 + (wl_z * 10) - (ct_z * 10)
    return max(50, min(200, round(risk)))


def _calc_support_risk(supervisor, coworker):
    """職場の支援判定図から健康リスクを算出"""
    nat_sv = NATIONAL_AVERAGES["supervisor_support"]
    nat_cw = NATIONAL_AVERAGES["coworker_support"]

    sv_z = (supervisor - nat_sv["mean"]) / nat_sv["sd"]
    cw_z = (coworker - nat_cw["mean"]) / nat_cw["sd"]

    # サポートが低いほどリスクが高い
    risk = 100 - (sv_z * 10) - (cw_z * 10)
    return max(50, min(200, round(risk)))


# =============================================================
# 個人結果のコメント生成
# =============================================================

COMMENTS = {
    "stressors": {
        "high": "仕事の負担やストレス要因がやや高い状態です。業務量の調整や、仕事の進め方について上司に相談してみましょう。",
        "moderate": "仕事のストレス要因は平均的な水準です。現在の状態を維持しながら、無理のない範囲で業務に取り組みましょう。",
        "low": "仕事のストレス要因は低い水準にあります。良好な状態が続いています。",
    },
    "reactions": {
        "high": "ストレスによる心身の反応がやや高い状態です。十分な休息をとり、リフレッシュする時間を意識的に設けましょう。症状が続く場合は、産業医への相談をお勧めします。",
        "moderate": "心身のストレス反応は平均的な水準です。日頃からセルフケアを心がけ、ストレスの蓄積を防ぎましょう。",
        "low": "心身のストレス反応は低い水準にあります。現在の生活リズムやストレス対処法が有効に機能しています。",
    },
    "support": {
        "high": "周囲からのサポートが十分に得られていない状態です。困ったことがあれば、上司や同僚、家族に気軽に相談してみましょう。",
        "moderate": "周囲からのサポートは平均的な水準です。引き続き、職場や家庭でのコミュニケーションを大切にしましょう。",
        "low": "周囲からのサポートが十分に得られています。良好な人間関係が維持されています。",
    },
    "overall": {
        "high": "現在、ストレスがやや高い状態にあります。一人で抱え込まず、周囲の人や専門家に相談することをお勧めします。必要に応じて、医師による面接指導を受けることができます。",
        "moderate": "ストレスの状態は概ね良好ですが、一部注意が必要な領域があります。セルフケアを心がけ、ストレスの蓄積を防ぎましょう。",
        "low": "ストレスの状態は良好です。引き続き、心身の健康を大切にしながら、仕事と生活のバランスを保ちましょう。",
    },
}


def get_result_comments(scores):
    """個人結果に対するコメントを生成"""
    a_total = scores["group_scores"]["A"]
    b_total = scores["group_scores"]["B"]
    c_total = scores["group_scores"]["C"]

    # A群: 9尺度 × 1-5 = 9-45, 中央27
    a_level = "high" if a_total >= 30 else ("moderate" if a_total >= 22 else "low")
    # B群: 6尺度 × 1-5 = 6-30, 中央18
    b_level = "high" if b_total >= 17 else ("moderate" if b_total >= 12 else "low")
    # C群: 3尺度 × 1-5 = 3-15, 中央9 (高い=サポート不足)
    c_level = "high" if c_total >= 10 else ("moderate" if c_total >= 7 else "low")

    overall = scores["stress_level"]

    return {
        "stressors": COMMENTS["stressors"][a_level],
        "reactions": COMMENTS["reactions"][b_level],
        "support": COMMENTS["support"][c_level],
        "overall": COMMENTS["overall"][overall],
    }
