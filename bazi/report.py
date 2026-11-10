"""Markdown report rendering."""
from __future__ import annotations

from .chart import Chart, life_stage
from .data import (BRANCH_PINYIN, ELEMENT_EN, ELEMENTS, HIDDEN_STEMS, PILLAR_ZH, STEM_ELEMENT,
                   STEM_PINYIN, STEMS, BRANCHES, TEN_GOD_EN, ZODIAC)
from .forecast import ROLE_EN, THEMES, annual_forecast
from .stars import STAR_EN


def _god(g: str) -> str:
    return f"{g} {TEN_GOD_EN[g]}"


def natal_section(c: Chart) -> str:
    L = []
    L.append(f"## Natal chart 命盘\n")
    L.append(f"- Birth: {c.birth_local:%Y-%m-%d %H:%M} (UTC{c.utc_offset:+g}), "
             f"gender {'male' if c.gender == 'M' else 'female'}")
    for n in c.notes:
        L.append(f"- {n}")
    L.append("")
    names = [n for n in ("hour", "day", "month", "year") if n in c.pillars]
    hdr = "| | " + " | ".join(f"{PILLAR_ZH[n]}柱 {n}" for n in names) + " |"
    L.append(hdr)
    L.append("|---" * (len(names) + 1) + "|")
    row = lambda label, f: L.append(f"| {label} | " + " | ".join(f(n) for n in names) + " |")
    row("Ten god (stem)", lambda n: "日主 Day Master" if n == "day" else _god(c.ten_god(c.pillars[n].stem)))
    row("Stem 天干", lambda n: f"**{c.pillars[n].stem}** {STEM_PINYIN[STEMS.index(c.pillars[n].stem)]} "
                               f"{ELEMENT_EN[STEM_ELEMENT[c.pillars[n].stem]]}")
    row("Branch 地支", lambda n: f"**{c.pillars[n].branch}** {BRANCH_PINYIN[BRANCHES.index(c.pillars[n].branch)]} "
                                 f"({ZODIAC[BRANCHES.index(c.pillars[n].branch)]})")
    row("Hidden 藏干", lambda n: " ".join(f"{s}·{c.ten_god(s)}" for s, _ in HIDDEN_STEMS[c.pillars[n].branch]))
    row("Nayin 纳音", lambda n: c.pillars[n].nayin)
    row("Stage 十二长生", lambda n: life_stage(c.day_master, c.pillars[n].branch))
    L.append("")

    st = c.strength()
    u = c.useful_elements()
    L.append("### Elements & strength")
    total = st["total"]
    L.append("| Element | Weight | Share | Role for Day Master |")
    L.append("|---|---|---|---|")
    for e in ELEMENTS:
        L.append(f"| {e} {ELEMENT_EN[e]} | {st['scores'][e]:.1f} | {st['scores'][e] / total:.0%} | {ROLE_EN[u['roles'][e]]} |")
    L.append("")
    dm = c.day_master
    L.append(f"- Day Master **{dm} {ELEMENT_EN[STEM_ELEMENT[dm]]}** "
             f"({'yang' if STEMS.index(dm) % 2 == 0 else 'yin'}); support share {st['ratio']:.0%} → "
             f"**{st['verdict']}**; {'in' if st['in_season'] else 'out of'} season "
             f"(month branch {c.pillars['month'].branch}, stage {life_stage(dm, c.pillars['month'].branch)}).")
    L.append(f"- Favourable elements 喜用: **{', '.join(f'{e} {ELEMENT_EN[e]}' for e in u['favourable'])}**")
    L.append(f"- Unfavourable elements 忌: {', '.join(f'{e} {ELEMENT_EN[e]}' for e in u['unfavourable'])}")
    if u["climate"]:
        L.append(f"- Climate adjustment 调候: chart needs {u['climate']} {ELEMENT_EN[u['climate']]}.")
    stars = c.stars()
    if stars:
        L.append("- Natal stars 神煞: " + "; ".join(f"{PILLAR_ZH[p]}支 {s} – {STAR_EN[s]}" for p, s in stars))
    L.append("")
    return "\n".join(L)


def luck_section(c: Chart) -> str:
    ls = c.luck_start()
    L = ["## Luck pillars 大运\n",
         f"Luck runs {'forward' if c.luck_direction() == 1 else 'backward'}; first pillar starts after "
         f"{ls['years']}y {ls['months']}m {ls['extra_days']}d (≈ {ls['start_date']:%Y-%m}).\n",
         "| Start | Age | Pillar | Stem god | Branch god | Elements |", "|---|---|---|---|---|---|"]
    u = c.useful_elements()
    for lp in c.luck_pillars(9):
        p = lp["pillar"]
        els = [STEM_ELEMENT[p.stem], STEM_ELEMENT[HIDDEN_STEMS[p.branch][0][0]]]
        tag = " ".join(("✓" if e in u["favourable"] else "✗" if e in u["unfavourable"] else "·") + ELEMENT_EN[e]
                       for e in els)
        L.append(f"| {lp['start']:%Y-%m} | {lp['start_age']} | **{p}** | {_god(c.ten_god(p.stem))} | "
                 f"{_god(c.ten_god(HIDDEN_STEMS[p.branch][0][0]))} | {tag} |")
    L.append("")
    return "\n".join(L)


def year_section(c: Chart, year: int) -> str:
    f = annual_forecast(c, year)
    a = f["annual"]
    p = f["pillar"]
    L = [f"## {year} {p} — {ZODIAC[BRANCHES.index(p.branch)]} year forecast 流年\n"]
    if f["luck"]:
        lp = f["luck"]["pillar"]
        L.append(f"- Active luck pillar: **{lp}** ({_god(c.ten_god(lp.stem))} / "
                 f"{_god(c.ten_god(HIDDEN_STEMS[lp.branch][0][0]))})")
    L.append(f"- Year stem {p.stem}: **{_god(a.stem_god)}**; year branch {p.branch}: **{_god(a.branch_god)}**; "
             f"Day Master stage: {a.life_stage}")
    L.append(f"- Overall rating: **{a.rating}** (score {a.score:+.2f})")
    from .verify import SHORT as _S, year_signals as _ys
    ysig = _ys(c, year)
    yl = [k for k in sorted(ysig, key=lambda k: -ysig[k]) if k not in ("good_year", "bad_year") and ysig[k] >= 0.4]
    L.append(f"- Likely event areas: {', '.join(f'{_S[k]} ({ysig[k]:.1f})' for k in yl[:4]) or 'no strong signals'}\n")
    L.append("### Themes")
    L.append(f"- **Visible (stem, H1 emphasis) – {a.stem_god}:** {THEMES[a.stem_god]}")
    if a.branch_god != a.stem_god:
        L.append(f"- **Underlying (branch, H2 emphasis) – {a.branch_god}:** {THEMES[a.branch_god]}")
    for n in a.notes:
        L.append(f"- {n}")
    if a.stars:
        L.append("- Stars activated: " + "; ".join(f"{s} – {STAR_EN[s]}" for s in a.stars))
    L.append("")
    if a.interactions:
        L.append("### Interactions with your chart")
        for where, desc, imp in a.interactions:
            L.append(f"- [{where}] {desc} ({'+' if imp > 0 else '−' if imp < 0 else '±'}{abs(imp):.2f})")
        L.append("")
    L.append("### Month by month 流月\n")
    from .verify import SHORT, year_signals
    L.append("| Solar month | Dates | Pillar | Stem / Branch god | Rating | Likely events | Key interactions |")
    L.append("|---|---|---|---|---|---|---|")
    for m in f["months"]:
        sig = year_signals(c, year, m.pillar)
        top = sorted((k for k in sig if k not in ("good_year", "bad_year") and sig[k] >= 0.4),
                     key=lambda k: -sig[k])[:3]
        likely = ", ".join(f"{SHORT[k]} ({sig[k]:.1f})" for k in top) or "quiet"
        keys = "; ".join(f"[{w}] {d.split(' — ')[0].split(' (')[0]}" for w, d, imp in m.interactions
                        if abs(imp) >= 0.2) or "—"
        L.append(f"| {m.label} ({m.jie}) | {m.start:%b %d} – {m.end:%b %d} | **{m.pillar}** | "
                 f"{m.stem_god} / {m.branch_god} | {m.rating} | {likely} | {keys} |")
    L.append("")
    best = sorted(f["months"], key=lambda m: -m.score)[:3]
    worst = sorted(f["months"], key=lambda m: m.score)[:3]
    L.append("**Best windows:** " + ", ".join(f"{m.start:%b %d}–{m.end:%b %d} ({m.pillar})" for m in best))
    L.append("")
    L.append("**Take care:** " + ", ".join(f"{m.start:%b %d}–{m.end:%b %d} ({m.pillar})" for m in worst))
    L.append("")
    return "\n".join(L)


def full_report(c: Chart, years: list[int]) -> str:
    parts = ["# BaZi 八字 report\n", natal_section(c), luck_section(c)]
    parts += [year_section(c, y) for y in years]
    parts.append("---\n_Computed with astronomical solar terms. Scores are a rules-based heuristic "
                 "(扶抑 + 调候 + interactions) meant as a starting point for interpretation._\n")
    return "\n".join(parts)
