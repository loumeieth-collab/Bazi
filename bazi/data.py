"""Static BaZi tables: stems, branches, elements, hidden stems, combinations."""

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
STEM_PINYIN = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
BRANCH_PINYIN = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]
ZODIAC = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake", "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]

ELEMENTS = ["木", "火", "土", "金", "水"]
ELEMENT_EN = {"木": "Wood", "火": "Fire", "土": "Earth", "金": "Metal", "水": "Water"}

STEM_ELEMENT = {s: ELEMENTS[i // 2] for i, s in enumerate(STEMS)}
STEM_YANG = {s: i % 2 == 0 for i, s in enumerate(STEMS)}
BRANCH_ELEMENT = dict(zip(BRANCHES, "水土木木土火火土金金土水"))
BRANCH_YANG = {b: i % 2 == 0 for i, b in enumerate(BRANCHES)}

# 地支藏干: (stem, weight) — main qi first.
HIDDEN_STEMS = {
    "子": [("癸", 1.0)],
    "丑": [("己", 0.6), ("癸", 0.3), ("辛", 0.1)],
    "寅": [("甲", 0.6), ("丙", 0.3), ("戊", 0.1)],
    "卯": [("乙", 1.0)],
    "辰": [("戊", 0.6), ("乙", 0.3), ("癸", 0.1)],
    "巳": [("丙", 0.6), ("庚", 0.3), ("戊", 0.1)],
    "午": [("丁", 0.7), ("己", 0.3)],
    "未": [("己", 0.6), ("丁", 0.3), ("乙", 0.1)],
    "申": [("庚", 0.6), ("壬", 0.3), ("戊", 0.1)],
    "酉": [("辛", 1.0)],
    "戌": [("戊", 0.6), ("辛", 0.3), ("丁", 0.1)],
    "亥": [("壬", 0.7), ("甲", 0.3)],
}

GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

NAYIN = [
    "海中金", "炉中火", "大林木", "路旁土", "剑锋金", "山头火", "涧下水", "城头土", "白蜡金", "杨柳木",
    "泉中水", "屋上土", "霹雳火", "松柏木", "长流水", "砂石金", "山下火", "平地木", "壁上土", "金箔金",
    "覆灯火", "天河水", "大驿土", "钗钏金", "桑柘木", "大溪水", "沙中土", "天上火", "石榴木", "大海水",
]

# 十二长生 order; start branch for each stem (yang forward, yin backward).
LIFE_STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
LIFE_START = {"甲": "亥", "丙": "寅", "戊": "寅", "庚": "巳", "壬": "申",
              "乙": "午", "丁": "酉", "己": "酉", "辛": "子", "癸": "卯"}

TEN_GOD_EN = {
    "比肩": "Friend", "劫财": "Rob Wealth", "食神": "Eating God", "伤官": "Hurting Officer",
    "偏财": "Indirect Wealth", "正财": "Direct Wealth", "七杀": "Seven Killings",
    "正官": "Direct Officer", "偏印": "Indirect Resource", "正印": "Direct Resource",
}

# Interactions
STEM_COMBOS = {frozenset("甲己"): "土", frozenset("乙庚"): "金", frozenset("丙辛"): "水",
               frozenset("丁壬"): "木", frozenset("戊癸"): "火"}
STEM_CLASHES = [frozenset(p) for p in ("甲庚", "乙辛", "丙壬", "丁癸")]
SIX_COMBOS = {frozenset("子丑"): "土", frozenset("寅亥"): "木", frozenset("卯戌"): "火",
              frozenset("辰酉"): "金", frozenset("巳申"): "水", frozenset("午未"): "火"}
SIX_CLASHES = [frozenset(p) for p in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")]
HARMS = [frozenset(p) for p in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")]
BREAKS = [frozenset(p) for p in ("子酉", "卯午", "辰丑", "未戌", "寅亥", "巳申")]
THREE_HARMONY = {"申子辰": "水", "亥卯未": "木", "寅午戌": "火", "巳酉丑": "金"}
THREE_MEETING = {"亥子丑": "水", "寅卯辰": "木", "巳午未": "火", "申酉戌": "金"}
PUNISHMENTS = [frozenset(p) for p in ("寅巳", "巳申", "寅申", "丑戌", "戌未", "丑未", "子卯")]
SELF_PUNISH = set("辰午酉亥")

# Symbolic stars
NOBLEMAN = {"甲": "丑未", "戊": "丑未", "庚": "丑未", "乙": "子申", "己": "子申",
            "丙": "亥酉", "丁": "亥酉", "壬": "卯巳", "癸": "卯巳", "辛": "午寅"}
ACADEMIC = {"甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
            "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯"}
PROSPERITY = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
              "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
BLADE = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}
# keyed by the trine group the year/day branch belongs to
PEACH = {"申子辰": "酉", "寅午戌": "卯", "巳酉丑": "午", "亥卯未": "子"}
HORSE = {"申子辰": "寅", "寅午戌": "申", "巳酉丑": "亥", "亥卯未": "巳"}
CANOPY = {"申子辰": "辰", "寅午戌": "戌", "巳酉丑": "丑", "亥卯未": "未"}

PILLAR_NAMES = ["year", "month", "day", "hour"]
PILLAR_ZH = {"year": "年", "month": "月", "day": "日", "hour": "时", "luck": "大运", "flow_year": "流年"}
PILLAR_DOMAIN = {
    "year": "family background, elders, wider network",
    "month": "career, parents, work environment",
    "day": "self, spouse/partner, home",
    "hour": "children, subordinates, projects, later life",
}
