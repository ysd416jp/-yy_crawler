"""
職業性ストレス簡易調査票（57項目標準版）
厚生労働省準拠
"""

# 回答選択肢の定義
CHOICES_A = [
    {"value": 4, "label": "そうだ"},
    {"value": 3, "label": "まあそうだ"},
    {"value": 2, "label": "ややちがう"},
    {"value": 1, "label": "ちがう"},
]

CHOICES_B = [
    {"value": 1, "label": "ほとんどなかった"},
    {"value": 2, "label": "ときどきあった"},
    {"value": 3, "label": "しばしばあった"},
    {"value": 4, "label": "ほとんどいつもあった"},
]

CHOICES_C = [
    {"value": 4, "label": "非常に"},
    {"value": 3, "label": "かなり"},
    {"value": 2, "label": "多少"},
    {"value": 1, "label": "全くない"},
]

CHOICES_D = [
    {"value": 4, "label": "満足"},
    {"value": 3, "label": "まあ満足"},
    {"value": 2, "label": "やや不満足"},
    {"value": 1, "label": "不満足"},
]

# 尺度（サブスケール）の定義
SUBSCALES = {
    # --- A群: 仕事のストレス要因 ---
    "workload_quantity": {
        "name": "心理的な仕事の負担（量）",
        "group": "A",
        "items": [1, 2, 3],
        "reverse": False,
    },
    "workload_quality": {
        "name": "心理的な仕事の負担（質）",
        "group": "A",
        "items": [4, 5, 6],
        "reverse": False,
    },
    "physical_demand": {
        "name": "自覚的な身体的負担度",
        "group": "A",
        "items": [7],
        "reverse": False,
    },
    "interpersonal": {
        "name": "職場の対人関係でのストレス",
        "group": "A",
        "items": [8, 9, 10],
        "reverse": False,
    },
    "environment": {
        "name": "職場環境によるストレス",
        "group": "A",
        "items": [11],
        "reverse": False,
    },
    "job_control": {
        "name": "仕事のコントロール度",
        "group": "A",
        "items": [12, 13, 14],
        "reverse": True,
    },
    "skill_utilization": {
        "name": "技能の活用度",
        "group": "A",
        "items": [15],
        "reverse": False,
    },
    "job_fitness": {
        "name": "仕事の適性度",
        "group": "A",
        "items": [16],
        "reverse": True,
    },
    "meaningfulness": {
        "name": "働きがい",
        "group": "A",
        "items": [17],
        "reverse": True,
    },
    # --- B群: 心身のストレス反応 ---
    "vitality": {
        "name": "活気",
        "group": "B",
        "items": [18, 19, 20],
        "reverse": True,
    },
    "irritability": {
        "name": "イライラ感",
        "group": "B",
        "items": [21, 22, 23],
        "reverse": False,
    },
    "fatigue": {
        "name": "疲労感",
        "group": "B",
        "items": [24, 25, 26],
        "reverse": False,
    },
    "anxiety": {
        "name": "不安感",
        "group": "B",
        "items": [27, 28, 29],
        "reverse": False,
    },
    "depression": {
        "name": "抑うつ感",
        "group": "B",
        "items": [30, 31, 32, 33, 34, 35],
        "reverse": False,
    },
    "somatic": {
        "name": "身体愁訴",
        "group": "B",
        "items": [36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46],
        "reverse": False,
    },
    # --- C群: 周囲のサポート ---
    "supervisor_support": {
        "name": "上司からのサポート",
        "group": "C",
        "items": [47, 50, 53],
        "reverse": True,
    },
    "coworker_support": {
        "name": "同僚からのサポート",
        "group": "C",
        "items": [48, 51, 54],
        "reverse": True,
    },
    "family_support": {
        "name": "家族・友人からのサポート",
        "group": "C",
        "items": [49, 52, 55],
        "reverse": True,
    },
    # --- D群: 満足度 ---
    "job_satisfaction": {
        "name": "仕事の満足度",
        "group": "D",
        "items": [56],
        "reverse": True,
    },
    "life_satisfaction": {
        "name": "家庭生活の満足度",
        "group": "D",
        "items": [57],
        "reverse": True,
    },
}

# 57項目の質問データ
QUESTIONS = [
    # ===== A群: 仕事のストレス要因 (Q1-Q17) =====
    # 回答: そうだ(4), まあそうだ(3), ややちがう(2), ちがう(1)
    {
        "number": 1,
        "text": "非常にたくさんの仕事をしなければならない",
        "group": "A",
        "choices": "A",
        "reverse": False,
    },
    {
        "number": 2,
        "text": "時間内に仕事が処理しきれない",
        "group": "A",
        "choices": "A",
        "reverse": False,
    },
    {
        "number": 3,
        "text": "一生懸命働かなければならない",
        "group": "A",
        "choices": "A",
        "reverse": False,
    },
    {
        "number": 4,
        "text": "かなり注意を集中する必要がある",
        "group": "A",
        "choices": "A",
        "reverse": False,
    },
    {
        "number": 5,
        "text": "高度の知識や技術が必要なむずかしい仕事だ",
        "group": "A",
        "choices": "A",
        "reverse": False,
    },
    {
        "number": 6,
        "text": "勤務時間中はいつも仕事のことを考えていなければならない",
        "group": "A",
        "choices": "A",
        "reverse": False,
    },
    {
        "number": 7,
        "text": "からだを大変よく使う仕事だ",
        "group": "A",
        "choices": "A",
        "reverse": False,
    },
    {
        "number": 8,
        "text": "私の部署内で意見のくい違いがある",
        "group": "A",
        "choices": "A",
        "reverse": False,
    },
    {
        "number": 9,
        "text": "私の部署と他の部署とはうまが合わない",
        "group": "A",
        "choices": "A",
        "reverse": False,
    },
    {
        "number": 10,
        "text": "私の職場の雰囲気は友好的である",
        "group": "A",
        "choices": "A",
        "reverse": True,
    },
    {
        "number": 11,
        "text": "私の職場の作業環境（騒音、照明、温度、換気など）はよくない",
        "group": "A",
        "choices": "A",
        "reverse": False,
    },
    {
        "number": 12,
        "text": "自分のペースで仕事ができる",
        "group": "A",
        "choices": "A",
        "reverse": True,
    },
    {
        "number": 13,
        "text": "自分で仕事の順番・やり方を決めることができる",
        "group": "A",
        "choices": "A",
        "reverse": True,
    },
    {
        "number": 14,
        "text": "職場の仕事の方針に自分の意見を反映できる",
        "group": "A",
        "choices": "A",
        "reverse": True,
    },
    {
        "number": 15,
        "text": "自分の技能や知識を仕事で使うことが少ない",
        "group": "A",
        "choices": "A",
        "reverse": False,
    },
    {
        "number": 16,
        "text": "仕事の内容は自分にあっている",
        "group": "A",
        "choices": "A",
        "reverse": True,
    },
    {
        "number": 17,
        "text": "働きがいのある仕事だ",
        "group": "A",
        "choices": "A",
        "reverse": True,
    },
    # ===== B群: 心身のストレス反応 (Q18-Q46) =====
    # 回答: ほとんどなかった(1), ときどきあった(2), しばしばあった(3), ほとんどいつもあった(4)
    {
        "number": 18,
        "text": "活気がわいてくる",
        "group": "B",
        "choices": "B",
        "reverse": True,
    },
    {
        "number": 19,
        "text": "元気がいっぱいだ",
        "group": "B",
        "choices": "B",
        "reverse": True,
    },
    {
        "number": 20,
        "text": "生き生きする",
        "group": "B",
        "choices": "B",
        "reverse": True,
    },
    {
        "number": 21,
        "text": "怒りを感じる",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 22,
        "text": "内心腹立たしい",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 23,
        "text": "イライラしている",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 24,
        "text": "ひどく疲れた",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 25,
        "text": "へとへとだ",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 26,
        "text": "だるい",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 27,
        "text": "気がはりつめている",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 28,
        "text": "不安だ",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 29,
        "text": "落ち着かない",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 30,
        "text": "ゆううつだ",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 31,
        "text": "何をするのも面倒だ",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 32,
        "text": "物事に集中できない",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 33,
        "text": "気分が晴れない",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 34,
        "text": "仕事が手につかない",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 35,
        "text": "悲しいと感じる",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 36,
        "text": "めまいがする",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 37,
        "text": "体のふしぶしが痛む",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 38,
        "text": "頭が重かったり頭痛がする",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 39,
        "text": "首筋や肩がこる",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 40,
        "text": "腰が痛い",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 41,
        "text": "目が疲れる",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 42,
        "text": "動悸や息切れがする",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 43,
        "text": "胃腸の具合が悪い",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 44,
        "text": "食欲がない",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 45,
        "text": "便秘や下痢をする",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    {
        "number": 46,
        "text": "よく眠れない",
        "group": "B",
        "choices": "B",
        "reverse": False,
    },
    # ===== C群: 周囲のサポート (Q47-Q55) =====
    # 3つの質問 × 3つの対象者
    # Q47-49: 気軽に話ができる  Q50-52: 頼りになる  Q53-55: きいてくれる
    {
        "number": 47,
        "text": "上司",
        "group": "C",
        "subtext": "次の人たちはどのくらい気軽に話ができますか？",
        "choices": "C",
        "reverse": False,
    },
    {
        "number": 48,
        "text": "職場の同僚",
        "group": "C",
        "subtext": "次の人たちはどのくらい気軽に話ができますか？",
        "choices": "C",
        "reverse": False,
    },
    {
        "number": 49,
        "text": "配偶者、家族、友人等",
        "group": "C",
        "subtext": "次の人たちはどのくらい気軽に話ができますか？",
        "choices": "C",
        "reverse": False,
    },
    {
        "number": 50,
        "text": "上司",
        "group": "C",
        "subtext": "あなたが困った時、次の人たちはどのくらい頼りになりますか？",
        "choices": "C",
        "reverse": False,
    },
    {
        "number": 51,
        "text": "職場の同僚",
        "group": "C",
        "subtext": "あなたが困った時、次の人たちはどのくらい頼りになりますか？",
        "choices": "C",
        "reverse": False,
    },
    {
        "number": 52,
        "text": "配偶者、家族、友人等",
        "group": "C",
        "subtext": "あなたが困った時、次の人たちはどのくらい頼りになりますか？",
        "choices": "C",
        "reverse": False,
    },
    {
        "number": 53,
        "text": "上司",
        "group": "C",
        "subtext": "あなたの個人的な問題を相談したら、次の人たちはどのくらいきいてくれますか？",
        "choices": "C",
        "reverse": False,
    },
    {
        "number": 54,
        "text": "職場の同僚",
        "group": "C",
        "subtext": "あなたの個人的な問題を相談したら、次の人たちはどのくらいきいてくれますか？",
        "choices": "C",
        "reverse": False,
    },
    {
        "number": 55,
        "text": "配偶者、家族、友人等",
        "group": "C",
        "subtext": "あなたの個人的な問題を相談したら、次の人たちはどのくらいきいてくれますか？",
        "choices": "C",
        "reverse": False,
    },
    # ===== D群: 満足度 (Q56-Q57) =====
    {
        "number": 56,
        "text": "仕事に満足だ",
        "group": "D",
        "choices": "D",
        "reverse": False,
    },
    {
        "number": 57,
        "text": "家庭生活に満足だ",
        "group": "D",
        "choices": "D",
        "reverse": False,
    },
]

# 群ごとの説明文
GROUP_HEADERS = {
    "A": {
        "title": "A. あなたの仕事についてうかがいます",
        "instruction": "最もあてはまるものを選んでください。",
    },
    "B": {
        "title": "B. 最近1か月間のあなたの状態についてうかがいます",
        "instruction": "最もあてはまるものを選んでください。",
    },
    "C": {
        "title": "C. あなたの周りの方々についてうかがいます",
        "instruction": "最もあてはまるものを選んでください。",
    },
    "D": {
        "title": "D. 満足度についてうかがいます",
        "instruction": "最もあてはまるものを選んでください。",
    },
}

CHOICE_SETS = {
    "A": CHOICES_A,
    "B": CHOICES_B,
    "C": CHOICES_C,
    "D": CHOICES_D,
}


def get_questions_by_group(group):
    return [q for q in QUESTIONS if q["group"] == group]
