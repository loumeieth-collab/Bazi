"""Four Pillars chart construction and natal analysis."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from . import astro
from .data import (BRANCHES, BRANCH_ELEMENT, CONTROLS, ELEMENTS, GENERATES, HIDDEN_STEMS,
                   LIFE_STAGES, LIFE_START, NAYIN, STEM_ELEMENT, STEM_YANG, STEMS)


@dataclass(frozen=True)
class Pillar:
    stem: str
    branch: str

    @classmethod
    def from_index(cls, i: int) -> "Pillar":
        i %= 60
        return cls(STEMS[i % 10], BRANCHES[i % 12])

    @property
    def index(self) -> int:
        s, b = STEMS.index(self.stem), BRANCHES.index(self.branch)
        return next(i for i in range(60) if i % 10 == s and i % 12 == b)

    @property
    def nayin(self) -> str:
        return NAYIN[self.index // 2]

    def __str__(self) -> str:
        return self.stem + self.branch


def ten_god(day_master: str, other: str) -> str:
    """Ten-god relationship of stem `other` relative to the day master."""
    dm_el, o_el = STEM_ELEMENT[day_master], STEM_ELEMENT[other]
    same = STEM_YANG[day_master] == STEM_YANG[other]
    if o_el == dm_el:
        return "比肩" if same else "劫财"
    if GENERATES[dm_el] == o_el:
        return "食神" if same else "伤官"
    if CONTROLS[dm_el] == o_el:
        return "偏财" if same else "正财"
    if CONTROLS[o_el] == dm_el:
        return "七杀" if same else "正官"
    return "偏印" if same else "正印"


def life_stage(stem: str, branch: str) -> str:
    start = BRANCHES.index(LIFE_START[stem])
    b = BRANCHES.index(branch)
    step = (b - start) % 12 if STEM_YANG[stem] else (start - b) % 12
    return LIFE_STAGES[step]


def element_role(day_master: str, element: str) -> str:
    dm = STEM_ELEMENT[day_master]
    if element == dm:
        return "companion"
    if GENERATES[element] == dm:
        return "resource"
    if GENERATES[dm] == element:
        return "output"
    if CONTROLS[dm] == element:
        return "wealth"
    return "power"


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

JIE_LONGITUDES = [(315 + 30 * k) % 360 for k in range(12)]  # 立春 惊蛰 ... 小寒 (寅..丑)
JIE_NAMES = ["立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "小寒"]


def jie_instants(year: int) -> list[tuple[str, float, int]]:
    """All 节 (month-starting terms) whose Gregorian date falls in `year`, sorted,
    as (name, jd_ut, month_branch_index)."""
    out = []
    for k, lon in enumerate(JIE_LONGITUDES):
        jd = astro.solar_term_jd(year, lon)
        out.append((JIE_NAMES[k], jd, (k + 2) % 12))
    return sorted(out, key=lambda x: x[1])


def li_chun(year: int) -> float:
    return astro.solar_term_jd(year, 315.0)


def year_pillar_at(jd_ut: float, greg_year: int) -> Pillar:
    y = greg_year if jd_ut >= li_chun(greg_year) else greg_year - 1
    return Pillar.from_index(y - 1984)  # 1984 = 甲子


def month_pillar_at(jd_ut: float, year_stem: str) -> Pillar:
    lon = astro.sun_longitude(jd_ut)
    k = int(((lon - 315) % 360) // 30)  # 0 = 寅
    first = (STEMS.index(year_stem) % 5) * 2 + 2  # 甲己之年丙作首
    return Pillar(STEMS[(first + k) % 10], BRANCHES[(k + 2) % 12])


def day_pillar_for_date(y: int, m: int, d: int) -> Pillar:
    jdn = int(astro.julian_day(datetime(y, m, d, 12)))
    return Pillar.from_index(jdn + 49)


def hour_stem(day_stem: str, branch_idx: int) -> str:
    return STEMS[((STEMS.index(day_stem) % 5) * 2 + branch_idx) % 10]


# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

@dataclass
class Chart:
    birth_local: datetime
    utc_offset: float
    gender: str  # "M" / "F"
    longitude: float | None = None
    zi_mode: str = "late"  # "late": day changes at 00:00 (晚子时); "early": day changes at 23:00
    hour_known: bool = True

    pillars: dict = field(init=False)
    solar_time: datetime = field(init=False)
    notes: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.gender = self.gender.upper()[0]
        utc = self.birth_local - timedelta(hours=self.utc_offset)
        self.jd_ut = astro.julian_day(utc)

        # Clock time used for the hour/day, optionally corrected to true solar time.
        t = self.birth_local
        if self.longitude is not None:
            lmt = utc + timedelta(hours=self.longitude / 15)
            t = lmt + timedelta(minutes=astro.equation_of_time_minutes(self.jd_ut))
            self.notes.append(
                f"True solar time at {self.longitude:.2f}°E: {t:%Y-%m-%d %H:%M} "
                f"(clock {self.birth_local:%H:%M}, UTC{self.utc_offset:+g})")
        self.solar_time = t

        # Year boundary is 立春 of the local Gregorian year
        yp = year_pillar_at(self.jd_ut, self.birth_local.year)
        mp = month_pillar_at(self.jd_ut, yp.stem)

        day_date = t.date()
        late_zi = t.hour == 23
        if late_zi and self.zi_mode == "early":
            day_date = day_date + timedelta(days=1)
        dp = day_pillar_for_date(day_date.year, day_date.month, day_date.day)

        self.pillars = {"year": yp, "month": mp, "day": dp}
        if self.hour_known:
            bidx = ((t.hour + 1) // 2) % 12
            stem_base = dp.stem
            if late_zi and self.zi_mode == "late":
                stem_base = STEMS[(STEMS.index(dp.stem) + 1) % 10]
                self.notes.append("Born in late 子 hour (23:00-24:00): day pillar kept, "
                                  "hour stem taken from the following day (晚子时).")
            self.pillars["hour"] = Pillar(hour_stem(stem_base, bidx), BRANCHES[bidx])

    # -- basic accessors -----------------------------------------------------
    @property
    def day_master(self) -> str:
        return self.pillars["day"].stem

    @property
    def dm_element(self) -> str:
        return STEM_ELEMENT[self.day_master]

    def ten_god(self, stem: str) -> str:
        return ten_god(self.day_master, stem)

    # -- element balance & strength -----------------------------------------
    def element_scores(self) -> dict[str, float]:
        """Weighted element tally. Stems 1.0, branches by hidden stems, month branch x2."""
        score = {e: 0.0 for e in ELEMENTS}
        for name, p in self.pillars.items():
            score[STEM_ELEMENT[p.stem]] += 1.0
            mult = 2.0 if name == "month" else 1.0
            for s, w in HIDDEN_STEMS[p.branch]:
                score[STEM_ELEMENT[s]] += w * mult
        return score

    def strength(self) -> dict:
        sc = self.element_scores()
        dm = self.dm_element
        res = next(e for e in ELEMENTS if GENERATES[e] == dm)
        support = sc[dm] + sc[res]
        total = sum(sc.values())
        ratio = support / total
        month_branch = self.pillars["month"].branch
        in_season = BRANCH_ELEMENT[month_branch] in (dm, res)
        if ratio >= 0.55:
            verdict = "strong"
        elif ratio <= 0.40:
            verdict = "weak"
        else:
            verdict = "balanced"
        return {"ratio": ratio, "support": support, "total": total, "verdict": verdict,
                "in_season": in_season, "scores": sc}

    def useful_elements(self) -> dict:
        """Heuristic favourable / unfavourable elements (扶抑 method) plus 调候."""
        st = self.strength()
        dm = self.dm_element
        role = {e: element_role(self.day_master, e) for e in ELEMENTS}
        by_role = {v: k for k, v in role.items()}
        sc = st["scores"]
        if st["verdict"] == "weak" or (st["verdict"] == "balanced" and st["ratio"] < 0.475):
            fav = [by_role["resource"], by_role["companion"]]
            unfav = [by_role["power"], by_role["wealth"], by_role["output"]]
            # Heaviest drain first
            unfav.sort(key=lambda e: -sc[e])
        else:
            drains = ["power", "output", "wealth"]
            fav = sorted((by_role[r] for r in drains), key=lambda e: sc[e])
            unfav = [by_role["resource"], by_role["companion"]]
        # 调候 (climate): winter births want fire, summer births want water.
        mb = self.pillars["month"].branch
        climate = None
        if mb in "亥子丑":
            climate = "火"
        elif mb in "巳午未":
            climate = "水"
        return {"favourable": fav, "unfavourable": unfav, "climate": climate, "roles": role}

    # -- luck pillars ---------------------------------------------------------
    def luck_direction(self) -> int:
        yang_year = STEM_YANG[self.pillars["year"].stem]
        male = self.gender == "M"
        return 1 if yang_year == male else -1

    def luck_start(self) -> dict:
        direction = self.luck_direction()
        y = self.birth_local.year
        jies = [j for yy in (y - 1, y, y + 1) for j in jie_instants(yy)]
        if direction == 1:
            target = min(j[1] for j in jies if j[1] > self.jd_ut)
            days = target - self.jd_ut
        else:
            target = max(j[1] for j in jies if j[1] <= self.jd_ut)
            days = self.jd_ut - target
        # 3 days = 1 year, 1 day = 4 months, 1 hour = 5 days
        total_months = days * 4
        yrs = int(total_months // 12)
        mos = total_months - yrs * 12
        start = self.birth_local + timedelta(days=days * 120)
        return {"days": days, "years": yrs, "months": int(mos),
                "extra_days": int((mos - int(mos)) * 30), "start_date": start}

    def luck_pillars(self, count: int = 10) -> list[dict]:
        ls = self.luck_start()
        d = self.luck_direction()
        mi = self.pillars["month"].index
        start = ls["start_date"]
        out = []
        for k in range(count):
            p = Pillar.from_index(mi + d * (k + 1))
            begin = start.replace(year=start.year + 10 * k) if not (start.month == 2 and start.day == 29) \
                else start + timedelta(days=3652.5 * k)
            out.append({"pillar": p, "start": begin,
                        "start_age": begin.year - self.birth_local.year,
                        "end_year": begin.year + 10})
        return out

    def luck_pillar_for_year(self, year: int) -> dict | None:
        """Luck pillar active for most of `year` (switch counted from its start year)."""
        current = None
        for lp in self.luck_pillars(12):
            if lp["start"].year <= year:
                current = lp
        return current

    # -- symbolic stars -------------------------------------------------------
    def stars(self) -> list[tuple[str, str]]:
        from .stars import natal_stars
        return natal_stars(self)
