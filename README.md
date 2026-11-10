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

## Verify the chart (定盘)

Birth times are often rounded, and conventions differ (clock vs true solar time,
晚子时 vs 子初换日). `verify` builds every plausible candidate chart, predicts which
kinds of big events each one expects in your past years, asks about the years where the
candidates disagree most, then ranks them by how well they match what actually happened.

```bash
python -m bazi verify --date 1990-05-01 --time 14:30 --gender F --tz 8 --longitude 101.69
```

You are shown a few years and answer with the event types that happened:

1. Career change · 2. Relationship · 3. Relocation · 4. Money gain/loss ·
5. Health · 6. Family (child born, parent ill/lost) · 7. Study / property

If the result is not conclusive, follow-up rounds target only the front-running
candidates (`--rounds`, `--followup`). Other options:

| Option | Meaning |
|---|---|
| `--all-hours` | birth hour unknown: test all 12 two-hour periods (automatic if `--time` is omitted) |
| `--vary-gender` | also test the opposite luck-pillar direction |
| `--event 2014:career --event 2019:family,relocation` | score events you remember (no prompts); `2016:none` marks a quiet year |
| `--event 2021:good_year --event 2018:bad_year` | overall good / hard years |
| `--decade 2010:2020:better` | the luck decade active in 2020 felt better (better/same/worse) than the one in 2010 |
| `--export-questions q.json` | write the questionnaire as JSON (for a form/app) |
| `--answers a.json` | score saved answers non-interactively |
| `--answers a.json --next-questions` | print adaptive follow-up years for saved answers |
| `--save-answers a.json` | keep interactive answers for later |

Answer file format — either a list of what happened (all categories considered asked):
`{"2014": ["career", "relocation"], "2019": []}` — or with the categories that were asked:
`{"2014": {"asked": ["career", "health", "family"], "happened": ["career"]}}`.
Categories: `career relationship relocation wealth health family study good_year bad_year`.
Decade comparisons go under `"decades": [[2010, 2020, "better"]]`.

Scoring is a transparent likelihood model: each candidate assigns each category a
probability (12% base rate + up to 70% from its chart signals: clashes/combinations on
the day, month, year and hour pillars, ten gods, 驿马/桃花/文昌, luck-pillar changes),
and answers update a prior that favours the time you gave.

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
