"""Annual (流年) and monthly (流月) forecasts against a natal chart."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import astro
from .chart import Chart, Pillar, jie_instants, life_stage
from .data import (BRANCH_ELEMENT, HIDDEN_STEMS, PILLAR_DOMAIN, PILLAR_ZH, STEM_ELEMENT,
                   STEMS, TEN_GOD_EN, ELEMENT_EN)
from .interactions import RELATION_EN, branch_relations, group_formations, stem_relations
from .stars import STAR_EN, stars_for_branch

THEMES = {
    "比肩": "Peers, independence and self-reliance. Good for asserting yourself and partnerships "
            "among equals; watch competition and spending to keep up with others.",
    "劫财": "Competition and bold moves. Networking and teamwork are energised, but money can "
            "leak through rivals, impulsive spending or lending. Guard shared finances.",
    "食神": "Creativity, enjoyment and output. A good time to produce, teach, showcase work and "
            "look after health and pleasure; results come through expression.",
    "伤官": "Talent pushing against rules. Innovation, performance and speaking out are favoured; "
            "friction with bosses, authority or contracts is the risk. Choose words carefully.",
    "偏财": "Opportunistic wealth: deals, side income, investing, sales. Active social life; "
            "money moves fast in both directions.",
    "正财": "Steady earned wealth: salary, savings, budgeting, responsibility. For men, a "
            "classic partner/marriage indicator.",
    "七杀": "Pressure, challenge and authority. Demanding targets, rivals or a tough boss; can "
            "bring promotion through hard effort. Mind stress, health and legal matters. For "
            "women, an indicator of an assertive partner.",
    "正官": "Recognition, status, structure and rules. Good for promotions, titles, formal "
            "commitments and reputation. For women, a classic husband/marriage indicator.",
    "偏印": "Unconventional learning, research, intuition, metaphysics. Introspective; can feel "
            "isolated or second-guess plans. Good for study and specialist skills.",
    "正印": "Support, mentors, qualifications, property and documents. Benefactors appear; "
            "good for study, certification, rest and recovery.",
}

ROLE_EN = {"companion": "companion (比劫)", "resource": "resource (印)", "output": "output (食伤)",
           "wealth": "wealth (财)", "power": "power/officer (官杀)"}


def _element_effect(el: str, useful: dict) -> float:
    if el in useful["favourable"]:
        return 1.0 if el == useful["favourable"][0] else 0.7
    if el in useful["unfavourable"]:
        return -1.0 if el == useful["unfavourable"][0] else -0.6
    return 0.0


@dataclass
class Period:
    label: str
    pillar: Pillar
    start: object = None
    end: object = None
    stem_god: str = ""
    branch_god: str = ""
    score: float = 0.0
    rating: str = ""
    interactions: list = field(default_factory=list)
    stars: list = field(default_factory=list)
    notes: list = field(default_factory=list)


def _rate(score: float) -> str:
    if score >= 1.2:
        return "★★★★★ excellent"
    if score >= 0.5:
        return "★★★★ favourable"
    if score > -0.5:
        return "★★★ mixed"
    if score > -1.2:
        return "★★ challenging"
    return "★ difficult"


def evaluate(chart: Chart, incoming: Pillar, label: str, context: dict[str, Pillar]) -> Period:
    """Score `incoming` against natal pillars plus extra context pillars (e.g. luck)."""
    useful = chart.useful_elements()
    dm = chart.day_master
    per = Period(label=label, pillar=incoming,
                 stem_god=chart.ten_god(incoming.stem),
                 branch_god=chart.ten_god(HIDDEN_STEMS[incoming.branch][0][0]))
    # base: element quality of stem and branch (branch weighted by hidden stems)
    s = 0.9 * _element_effect(STEM_ELEMENT[incoming.stem], useful)
    for hs, w in HIDDEN_STEMS[incoming.branch]:
        s += 1.1 * w * _element_effect(STEM_ELEMENT[hs], useful)
    if useful["climate"]:
        clim = useful["climate"]
        if STEM_ELEMENT[incoming.stem] == clim or BRANCH_ELEMENT[incoming.branch] == clim:
            s += 0.2
            per.notes.append(f"Brings {ELEMENT_EN[clim]}, which warms/balances the chart's climate (调候).")

    pillars = {**chart.pillars, **context}
    for name, p in pillars.items():
        zh = PILLAR_ZH.get(name, name)
        for rel, el in stem_relations(incoming.stem, p.stem):
            desc = f"{incoming.stem}{p.stem} {RELATION_EN[rel]}"
            if el:
                desc += f" → {ELEMENT_EN[el]}"
            impact = 0.0
            if rel == "天干合":
                impact = 0.3 * _element_effect(el, useful)
                if name == "day":
                    desc += " (this period 'binds' you: commitments, partnerships, being pulled in)"
            elif rel == "天干冲":
                impact = -0.35 if name in ("day", "month") else -0.2
            per.interactions.append((f"{zh}干", desc, impact))
            s += impact
        for rel, el in branch_relations(incoming.branch, p.branch):
            desc = f"{incoming.branch}{p.branch} {RELATION_EN[rel]}"
            if el:
                desc += f" → {ELEMENT_EN[el]}"
            weight = {"day": 1.0, "month": 0.9, "year": 0.6, "hour": 0.7}.get(name, 0.8)
            impact = 0.0
            if rel == "六冲":
                impact = -0.45 * weight
                # clashing away an unfavourable element softens the blow
                if BRANCH_ELEMENT[p.branch] in useful["unfavourable"]:
                    impact *= 0.6
                if name in PILLAR_DOMAIN:
                    desc += f" — stirs {PILLAR_DOMAIN[name]}"
            elif rel in ("刑", "自刑"):
                impact = -0.25 * weight
            elif rel in ("害", "破"):
                impact = -0.15 * weight
            elif rel in ("六合", "半三合"):
                impact = 0.25 * weight + 0.25 * _element_effect(el, useful)
            elif rel == "伏吟":
                impact = -0.1
                desc += " — repeating themes, delays, déjà vu"
            if rel != "伏吟" or name in ("day", "month", "luck"):
                per.interactions.append((f"{zh}支", desc, impact))
                s += impact
    existing = group_formations([p.branch for p in pillars.values()])
    for kind, trio, el in group_formations([p.branch for p in pillars.values()] + [incoming.branch]):
        if incoming.branch in trio and (kind, trio, el) not in existing:
            impact = 0.5 * _element_effect(el, useful)
            per.interactions.append(("局", f"{trio} {RELATION_EN[kind]} → {ELEMENT_EN[el]}", impact))
            s += impact

    yb, db = chart.pillars["year"].branch, chart.pillars["day"].branch
    per.stars = stars_for_branch(dm, yb, db, incoming.branch)
    for st in per.stars:
        if st in ("天乙贵人", "文昌", "禄神"):
            s += 0.15
    per.score = s
    per.rating = _rate(s)
    per.life_stage = life_stage(dm, incoming.branch)
    return per


def year_pillar(year: int) -> Pillar:
    return Pillar.from_index(year - 1984)


def annual_forecast(chart: Chart, year: int) -> dict:
    lp = chart.luck_pillar_for_year(year)
    context = {"luck": lp["pillar"]} if lp else {}
    yp = year_pillar(year)
    annual = evaluate(chart, yp, f"{year} {yp}", context)

    # monthly: from 立春 of `year` to 立春 of year+1
    jies = [j for yy in (year, year + 1) for j in jie_instants(yy)]
    start_idx = next(i for i, j in enumerate(jies) if j[0] == "立春")
    months = []
    first = (STEMS.index(yp.stem) % 5) * 2 + 2
    for k in range(12):
        name, jd, bidx = jies[start_idx + k]
        nxt = jies[start_idx + k + 1][1]
        mp = Pillar(STEMS[(first + k) % 10], "寅卯辰巳午未申酉戌亥子丑"[k])
        off = chart.utc_offset / 24
        per = evaluate(chart, mp, f"Month {k + 1}", {**context, "flow_year": yp})
        per.start = astro.from_julian_day(jd + off)
        per.end = astro.from_julian_day(nxt + off)
        per.jie = name
        months.append(per)
    return {"year": year, "pillar": yp, "luck": lp, "annual": annual, "months": months}
