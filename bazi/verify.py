"""Chart verification (定盘 / birth-time rectification).

Builds several candidate charts for the same person (clock vs true solar time,
晚子/子初 conventions, neighbouring 2-hour periods, optionally both genders),
predicts which life-event categories each candidate expects in past years,
picks the years where candidates disagree most, asks the user what actually
happened, and ranks candidates by likelihood.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from .chart import Chart, Pillar
from .data import HIDDEN_STEMS, SIX_CLASHES, STEM_CLASHES
from .forecast import evaluate, year_pillar
from .interactions import branch_relations, group_formations, stem_relations
from .stars import stars_for_branch

CATEGORIES = {
    "career": "Career change: new job, promotion, job loss, starting/closing a business",
    "relationship": "Relationship: new partner, marriage, engagement, breakup or divorce",
    "relocation": "Relocation: moving house, emigrating, long-term overseas stay",
    "wealth": "Money: notable financial windfall or significant loss",
    "health": "Health: illness, injury, surgery or accident (you)",
    "family": "Family: birth of a child, illness/loss of a parent or elder, family upheaval",
    "study": "Study/property: graduation, major exam or qualification, buying property",
    "good_year": "Overall a good year: things went your way",
    "bad_year": "Overall a hard year: stress, setbacks, losses",
}
SHORT = {
    "career": "Career change", "relationship": "Relationship change", "relocation": "Moved / relocated",
    "wealth": "Big money gain/loss", "health": "Health issue", "family": "Family event",
    "study": "Study / property", "good_year": "Good year overall", "bad_year": "Hard year overall",
}

BASE_RATE = 0.12      # chance an event category happens in a "quiet" year
SIGNAL_GAIN = 0.70    # extra probability at full predicted intensity


@dataclass
class Candidate:
    label: str
    chart: Chart
    prior: float

    @property
    def key(self) -> str:
        return " ".join(str(self.chart.pillars[k]) for k in ("year", "month", "day", "hour")
                        if k in self.chart.pillars) + f" {self.chart.gender}"


# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------

def build_candidates(birth: datetime, tz: float, gender: str, longitude: float | None = None,
                     all_hours: bool = False, vary_gender: bool = False) -> list[Candidate]:
    raw: list[tuple[str, dict, float]] = []
    genders = ["M", "F"] if vary_gender else [gender]
    if all_hours:
        day = birth.replace(hour=0, minute=30)
        for h in range(12):
            t = day + timedelta(hours=2 * h)
            raw.append((f"{t:%H}:30 clock time", {"birth_local": t}, 1.0))
    else:
        raw.append(("as given, clock time", {"birth_local": birth}, 1.0))
        if longitude is not None:
            raw.append(("as given, true solar time", {"birth_local": birth, "longitude": longitude}, 1.0))
        for z in ("late", "early"):
            raw.append((f"as given, clock time, 23:00 rule={z}", {"birth_local": birth, "zi_mode": z}, 0.8))
        for delta in (-2, 2):
            t = birth + timedelta(hours=delta)
            raw.append((f"birth time off by {delta:+d}h ({t:%H:%M})", {"birth_local": t}, 0.4))
            if longitude is not None:
                raw.append((f"birth time off by {delta:+d}h, true solar time",
                            {"birth_local": t, "longitude": longitude}, 0.4))
    out: dict[str, Candidate] = {}
    for g in genders:
        for label, kw, prior in raw:
            kw = {"zi_mode": "late", **kw}
            c = Chart(utc_offset=tz, gender=g, **kw)
            lab = label + ("" if not vary_gender else f", {'male' if g == 'M' else 'female'}")
            cand = Candidate(lab, c, prior * (1.0 if g == gender else 0.5))
            if cand.key in out:  # same pillars → merge
                out[cand.key].prior += cand.prior
                if lab not in out[cand.key].label:
                    out[cand.key].label += f" / {lab}"
            else:
                out[cand.key] = cand
    total = sum(c.prior for c in out.values())
    for c in out.values():
        c.prior /= total
    return list(out.values())


# ---------------------------------------------------------------------------
# Event signals
# ---------------------------------------------------------------------------

def _spouse_gods(chart: Chart) -> set[str]:
    return {"正财", "偏财"} if chart.gender == "M" else {"正官", "七杀"}


def _child_gods(chart: Chart) -> set[str]:
    """Classical child star: officers for a man, output stars for a woman."""
    return {"正官", "七杀"} if chart.gender == "M" else {"食神", "伤官"}


def year_signals(chart: Chart, year: int) -> dict[str, float]:
    """Predicted intensity (0..1) of each event category for `year`."""
    s = {k: 0.0 for k in CATEGORIES}
    yp = year_pillar(year)
    p = chart.pillars
    gods = {chart.ten_god(yp.stem), chart.ten_god(HIDDEN_STEMS[yp.branch][0][0])}

    def rels(name):
        return {r for r, _ in branch_relations(yp.branch, p[name].branch)} if name in p else set()

    day, month, yr, hour = rels("day"), rels("month"), rels("year"), rels("hour")

    # day pillar: self, spouse, home
    if "六冲" in day:
        s["relationship"] += 0.55; s["relocation"] += 0.45; s["health"] += 0.2
    if day & {"六合", "半三合"}:
        s["relationship"] += 0.45
    if day & {"刑", "自刑"}:
        s["health"] += 0.3; s["relationship"] += 0.15
    if day & {"害", "破"}:
        s["relationship"] += 0.15; s["health"] += 0.1
    if any(r == "天干合" for r, _ in stem_relations(yp.stem, chart.day_master)):
        s["relationship"] += 0.35
    if frozenset((yp.stem, chart.day_master)) in STEM_CLASHES:
        s["health"] += 0.2; s["career"] += 0.15
    if "六冲" in day and frozenset((yp.stem, chart.day_master)) in STEM_CLASHES:  # 天克地冲
        for k in ("career", "relocation", "health"):
            s[k] += 0.2
    if gods & _spouse_gods(chart):
        s["relationship"] += 0.25
    # spouse star of the year combined away by a natal stem (合财 / 合官): partner "taken"
    if chart.ten_god(yp.stem) in _spouse_gods(chart):
        for name in ("year", "month", "hour"):
            if any(r == "天干合" for r, _ in stem_relations(yp.stem, p[name].stem) if name in p):
                s["relationship"] += 0.2
                break
    # year completes a three-harmony / directional frame that absorbs the spouse palace
    natal_branches = [q.branch for q in p.values()]
    before = group_formations(natal_branches)
    for kind, trio, el in group_formations(natal_branches + [yp.branch]):
        if (kind, trio, el) not in before and yp.branch in trio and p["day"].branch in trio:
            s["relationship"] += 0.3
            break

    # month pillar: career, parents
    if "六冲" in month:
        s["career"] += 0.55; s["family"] += 0.2
    if month & {"刑", "害", "破"}:
        s["career"] += 0.25
    if month & {"六合", "半三合"}:
        s["career"] += 0.2
    if gods & {"七杀", "伤官"}:
        s["career"] += 0.3
    if "正官" in gods:
        s["career"] += 0.25

    # year pillar: family, elders
    if "六冲" in yr:
        s["family"] += 0.4; s["relocation"] += 0.2
    if "伏吟" in yr:  # 本命年
        s["family"] += 0.15; s["health"] += 0.15

    # hour pillar: children, projects
    if "六冲" in hour:
        s["family"] += 0.5; s["career"] += 0.15
    if hour & {"六合", "半三合"}:
        s["family"] += 0.35
    if hour & {"刑", "自刑", "害"}:
        s["family"] += 0.2
    if chart.ten_god(yp.stem) in _child_gods(chart):
        s["family"] += 0.2
    if "hour" in p:
        for r, _ in stem_relations(yp.stem, p["hour"].stem):
            s["family"] += 0.15 if r == "天干冲" else 0.1
            s["career"] += 0.1

    # stars and ten gods
    stars = stars_for_branch(chart.day_master, p["year"].branch, p["day"].branch, yp.branch)
    if "驿马" in stars:
        s["relocation"] += 0.35
    if "桃花" in stars:
        s["relationship"] += 0.25
    if "文昌" in stars:
        s["study"] += 0.25
    if gods & {"正财", "偏财"}:
        s["wealth"] += 0.35
    if gods & {"劫财"}:
        s["wealth"] += 0.2
    if gods & {"正印", "偏印"}:
        s["study"] += 0.4

    # luck pillar context
    lp = chart.luck_pillar_for_year(year)
    if lp:
        if lp["start"].year == year:
            s["career"] += 0.2; s["relocation"] += 0.2
        if frozenset((yp.branch, lp["pillar"].branch)) in SIX_CLASHES:
            s["career"] += 0.15; s["relocation"] += 0.15
        ctx = {"luck": lp["pillar"]}
    else:
        ctx = {}
    score = evaluate(chart, yp, str(year), ctx).score
    s["good_year"] = max(0.0, score / 2)
    s["bad_year"] = max(0.0, -score / 2)
    if score < -1.0:
        s["health"] += 0.3; s["wealth"] += 0.15
    elif score < -0.5:
        s["health"] += 0.15
    return {k: min(1.0, v) for k, v in s.items()}


def probability(intensity: float) -> float:
    return BASE_RATE + SIGNAL_GAIN * intensity


# ---------------------------------------------------------------------------
# Question selection & scoring
# ---------------------------------------------------------------------------

def select_questions(cands: list[Candidate], years: list[int], n: int = 6,
                     options_per_year: int = 4, weights: dict[str, float] | None = None,
                     exclude: dict[int, set[str]] | None = None) -> list[dict]:
    """Pick the `n` years (and categories) that best separate the candidates.

    `weights` (candidate key -> probability) focuses the choice on the
    candidates still in contention; `exclude` maps year -> categories already asked."""
    w = weights or {c.key: c.prior for c in cands}
    exclude = exclude or {}
    rows = []
    for y in years:
        open_cats = [k for k in CATEGORIES if k not in exclude.get(y, set())]
        if not open_cats:
            continue
        sig = {c.key: year_signals(c.chart, y) for c in cands}
        cat_score = {}
        for cat in open_cats:
            ps = [probability(sig[c.key][cat]) for c in cands]
            mean = sum(w[c.key] * pr for c, pr in zip(cands, ps))
            var = sum(w[c.key] * (pr - mean) ** 2 for c, pr in zip(cands, ps))
            cat_score[cat] = var + 0.002 * mean  # discrimination, memorability as tie-break
        cats = sorted(open_cats, key=lambda k: -cat_score[k])[:options_per_year]
        rows.append({"year": y, "pillar": str(year_pillar(y)), "categories": cats,
                     "score": sum(cat_score[k] for k in cats)})
    rows.sort(key=lambda r: -r["score"])
    chosen = sorted(rows[:n], key=lambda r: r["year"])
    for r in chosen:
        r.pop("score")
    return chosen


def next_questions(cands: list[Candidate], years: list[int], answers: dict, n: int = 4) -> list[dict]:
    """Adaptive follow-up: choose new years that split the current front-runners."""
    if answers:
        weights = {r["candidate"].key: r["posterior"] for r in score_candidates(cands, answers)}
    else:
        weights = None
    asked = {y: set(a["asked"]) for y, a in normalise_answers(answers).items()}
    return select_questions(cands, years, n=n, weights=weights, exclude=asked)


def merge_answer(answers: dict, year: int, asked: list[str], happened: list[str]) -> None:
    """Add an answer for `year`, combining with any earlier answer for that year."""
    prev = answers.get(str(year))
    if prev is not None:
        prev = normalise_answers({str(year): prev})[year]
        asked = list(dict.fromkeys(list(prev["asked"]) + list(asked)))
        happened = list(dict.fromkeys(list(prev["happened"]) + list(happened)))
    answers[str(year)] = {"asked": asked, "happened": happened}


DECADE_RESULTS = ("better", "same", "worse")


def decade_probability(chart: Chart, earlier: int, later: int, result: str) -> float:
    """P(user judges the luck pillar active in `later` better/same/worse than the one in `earlier`)."""
    from .forecast import evaluate as _ev
    a = chart.luck_pillar_for_year(earlier)
    b = chart.luck_pillar_for_year(later)
    if not a or not b:
        return 1 / 3
    d = _ev(chart, b["pillar"], "", {}).score - _ev(chart, a["pillar"], "", {}).score
    logits = {"better": 1.5 * d, "same": 0.5, "worse": -1.5 * d}
    z = sum(math.exp(v) for v in logits.values())
    return 0.05 + 0.85 * math.exp(logits[result]) / z


def normalise_answers(answers: dict) -> dict[int, dict]:
    """Accept {"2014": ["career"]} (all categories asked) or
    {"2014": {"asked": [...], "happened": [...]}}."""
    out = {}
    for y, v in answers.items():
        if y == "decades":
            continue
        if isinstance(v, dict):
            asked, happened = list(v.get("asked", CATEGORIES)), list(v.get("happened", []))
        else:
            asked, happened = list(CATEGORIES), list(v)
        bad = set(asked + happened) - set(CATEGORIES)
        if bad:
            raise ValueError(f"unknown categories for {y}: {sorted(bad)}")
        out[int(y)] = {"asked": asked, "happened": set(happened)}
    return out


def score_candidates(cands: list[Candidate], answers: dict) -> list[dict]:
    ans = normalise_answers(answers)
    results = []
    for c in cands:
        ll = math.log(c.prior)
        hits, misses = [], []
        for y, a in ans.items():
            sig = year_signals(c.chart, y)
            for cat in a["asked"]:
                pr = probability(sig[cat])
                if cat in a["happened"]:
                    ll += math.log(pr)
                    (hits if sig[cat] >= 0.3 else misses).append(f"{y} {cat}")
                else:
                    ll += math.log(1 - pr)
                    if sig[cat] >= 0.5:
                        misses.append(f"{y} no {cat} (predicted)")
        for earlier, later, result in answers.get("decades", []):
            if result not in DECADE_RESULTS:
                raise ValueError(f"decade result must be one of {DECADE_RESULTS}")
            pr = decade_probability(c.chart, int(earlier), int(later), result)
            ll += math.log(pr)
            (hits if pr >= 0.4 else misses).append(f"{later}s {result} than {earlier}s")
        results.append({"candidate": c, "loglik": ll, "hits": hits, "misses": misses})
    m = max(r["loglik"] for r in results)
    z = sum(math.exp(r["loglik"] - m) for r in results)
    for r in results:
        r["posterior"] = math.exp(r["loglik"] - m) / z
    results.sort(key=lambda r: -r["posterior"])
    return results


def verdict(results: list[dict]) -> str:
    top = results[0]["posterior"]
    second = results[1]["posterior"] if len(results) > 1 else 0.0
    if top >= 0.6 and top >= 2 * second:
        return "confident"
    if top >= 0.4:
        return "leaning"
    return "inconclusive — answer more years"


def render_results(results: list[dict]) -> str:
    L = ["## Verification result 定盘\n",
         f"Verdict: **{verdict(results)}**\n",
         "| Rank | Probability | Pillars (Y M D H, gender) | Candidate | Supported by |",
         "|---|---|---|---|---|"]
    for i, r in enumerate(results, 1):
        c = r["candidate"]
        L.append(f"| {i} | {r['posterior']:.0%} | {c.key} | {c.label} | "
                 f"{', '.join(r['hits'][:5]) or '—'} |")
    best = results[0]["candidate"]
    L.append("")
    L.append(f"Best match: **{best.key}** ({best.label}).")
    if results[0]["misses"]:
        L.append(f"Not explained by the best match: {', '.join(results[0]['misses'][:6])}.")
    L.append("")
    return "\n".join(L)
