"""Detect stem/branch interactions between an incoming pillar and a set of pillars."""
from __future__ import annotations

from .data import (BREAKS, HARMS, PUNISHMENTS, SELF_PUNISH, SIX_CLASHES, SIX_COMBOS,
                   STEM_CLASHES, STEM_COMBOS, THREE_HARMONY, THREE_MEETING)


def stem_relations(a: str, b: str) -> list[tuple[str, str | None]]:
    pair = frozenset((a, b))
    out = []
    if pair in STEM_COMBOS:
        out.append(("天干合", STEM_COMBOS[pair]))
    if pair in STEM_CLASHES:
        out.append(("天干冲", None))
    return out


def branch_relations(a: str, b: str) -> list[tuple[str, str | None]]:
    pair = frozenset((a, b))
    out = []
    if a == b:
        if a in SELF_PUNISH:
            out.append(("自刑", None))
        out.append(("伏吟", None))
        return out
    if pair in SIX_COMBOS:
        out.append(("六合", SIX_COMBOS[pair]))
    if pair in SIX_CLASHES:
        out.append(("六冲", None))
    if pair in PUNISHMENTS:
        out.append(("刑", None))
    if pair in HARMS:
        out.append(("害", None))
    if pair in BREAKS:
        out.append(("破", None))
    for trio, el in THREE_HARMONY.items():
        if a in trio and b in trio and trio[1] in (a, b):  # half-combo needs the middle branch
            out.append(("半三合", el))
    return out


def group_formations(branches: list[str]) -> list[tuple[str, str, str]]:
    """Full three-harmony / directional (三合 / 三会) formations present in `branches`."""
    s = set(branches)
    out = []
    for trio, el in THREE_HARMONY.items():
        if set(trio) <= s:
            out.append(("三合局", trio, el))
    for trio, el in THREE_MEETING.items():
        if set(trio) <= s:
            out.append(("三会局", trio, el))
    return out


RELATION_EN = {
    "天干合": "stem combination", "天干冲": "stem clash", "六合": "six-harmony combination",
    "六冲": "clash", "刑": "punishment", "自刑": "self-punishment", "害": "harm",
    "破": "break", "半三合": "half three-harmony", "伏吟": "repetition (伏吟)",
    "三合局": "full three-harmony frame", "三会局": "directional frame",
}
