# BaZi 八字 — Four Pillars chart & yearly forecast

A self-contained Python (3.10+, no runtime dependencies) BaZi engine:

- **Astronomical calendar**: solar terms (节气) computed from the Sun's apparent longitude
  (Meeus, with ΔT), so year/month pillars switch at the exact 立春 / 节 instants.
- **Four pillars** with optional **true solar time** (`--longitude`) and a choice of
  late-Zi-hour convention (`--zi late|early`).
- **Natal analysis**: ten gods, hidden stems, nayin, twelve life stages, weighted
  element balance, Day Master strength, favourable/unfavourable elements (扶抑 + 调候),
  symbolic stars (贵人, 文昌, 禄, 羊刃, 桃花, 驿马, 华盖).
- **Luck pillars 大运** with exact start age (3 days = 1 year).
- **Yearly forecast 流年** + **12 solar months 流月**: ten-god themes, clashes,
  combinations, punishments, harms, three-harmony/directional frames against the natal
  chart, the active luck pillar and the flowing year, with a heuristic rating.

## Usage

```bash
python -m bazi --date 1990-05-01 --time 14:30 --gender F --tz 8 --year 2027
python -m bazi --date 1990-05-01 --time 14:30 --gender M --tz 8 \
    --longitude 101.69 --year 2026 --year 2027 -o report.md
```

| Option | Meaning |
|---|---|
| `--tz` | UTC offset of the birth clock time (e.g. 8 for Malaysia/Singapore/China) |
| `--longitude` | birthplace longitude °E; converts clock time to true solar time for the hour/day |
| `--zi late` | (default) 23:00–24:00 keeps the same day pillar (晚子时) |
| `--zi early` | day changes at 23:00 (子初换日) |
| `--year` | forecast year, repeatable (default: this year and next) |

Omit `--time` if the birth hour is unknown; the hour pillar is then left out.

## Tests

```bash
pip install pytest lunar_python   # lunar_python is only used as a reference oracle
python -m pytest -q
```

The suite cross-checks 3,000 random charts (1920–2030) and luck pillars against
`lunar_python`, and solar-term instants to within 10 minutes.

## Caveat

Favourability scores are a transparent rules-based heuristic intended as a starting
point for interpretation, not a substitute for a practitioner's judgement.
