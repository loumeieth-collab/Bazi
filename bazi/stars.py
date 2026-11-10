"""Common symbolic stars (神煞)."""
from __future__ import annotations

from .data import (ACADEMIC, BLADE, CANOPY, HORSE, NOBLEMAN, PEACH, PROSPERITY)

STAR_EN = {
    "天乙贵人": "Nobleman (help from benefactors)",
    "文昌": "Academic star (learning, exams, writing)",
    "禄神": "Prosperity star (salary, stable income)",
    "羊刃": "Goat Blade (drive, competition, injury risk)",
    "桃花": "Peach Blossom (charm, romance, popularity)",
    "驿马": "Travelling Horse (movement, relocation, travel)",
    "华盖": "Canopy (spirituality, solitude, art)",
}


def _group(branch: str) -> str:
    return next(g for g in PEACH if branch in g)


def stars_for_branch(day_stem: str, year_branch: str, day_branch: str, branch: str) -> list[str]:
    out = []
    if branch in NOBLEMAN[day_stem]:
        out.append("天乙贵人")
    if ACADEMIC[day_stem] == branch:
        out.append("文昌")
    if PROSPERITY[day_stem] == branch:
        out.append("禄神")
    if BLADE.get(day_stem) == branch:
        out.append("羊刃")
    for base in {year_branch, day_branch}:
        g = _group(base)
        for name, table in (("桃花", PEACH), ("驿马", HORSE), ("华盖", CANOPY)):
            if table[g] == branch and name not in out:
                out.append(name)
    return out


def natal_stars(chart) -> list[tuple[str, str]]:
    p = chart.pillars
    res = []
    for name, pil in p.items():
        for s in stars_for_branch(chart.day_master, p["year"].branch, p["day"].branch, pil.branch):
            res.append((name, s))
    return res
