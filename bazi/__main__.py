"""Command line.

  python -m bazi [chart] --date 1990-05-01 --time 14:30 --gender F --year 2027
  python -m bazi verify  --date 1990-05-01 --time 14:30 --gender F [--answers a.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from .chart import Chart
from .report import full_report


def _common(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--date", required=True, help="birth date YYYY-MM-DD (Gregorian)")
    ap.add_argument("--time", default=None, help="birth clock time HH:MM (omit if unknown)")
    ap.add_argument("--gender", required=True, choices=["M", "F", "m", "f"])
    ap.add_argument("--tz", type=float, default=8.0, help="UTC offset in hours at birth (default 8)")
    ap.add_argument("--longitude", type=float, default=None,
                    help="birthplace longitude (°E) to use true solar time for the hour")


def _birth(a) -> datetime:
    return datetime.strptime(f"{a.date} {a.time or '12:00'}", "%Y-%m-%d %H:%M")


def _write(md: str, path: str | None) -> None:
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"wrote {path}")
    else:
        print(md)


def cmd_chart(a) -> None:
    c = Chart(_birth(a), a.tz, a.gender, longitude=a.longitude, zi_mode=a.zi, hour_known=a.time is not None)
    years = a.year or [datetime.now().year, datetime.now().year + 1]
    _write(full_report(c, years), a.output)


def _ask_interactively(questions: list[dict], answers: dict, show_help: bool = True) -> dict:
    from .verify import CATEGORIES, merge_answer
    keys = list(CATEGORIES)
    if show_help:
        print("\nFor each year, enter the numbers of everything that happened (e.g. 1,3),")
        print("0 for 'nothing notable', or press Enter to skip a year you can't remember.\n")
        for i, k in enumerate(keys, 1):
            print(f"  {i}. {CATEGORIES[k]}")
    for q in questions:
        while True:
            raw = input(f"\n{q['year']} ({q['pillar']}) > ").strip()
            if raw == "":
                break
            try:
                nums = [int(x) for x in raw.replace(" ", "").split(",") if x]
                if any(n < 0 or n > len(keys) for n in nums):
                    raise ValueError
            except ValueError:
                print("  please enter numbers like 1,4 or 0")
                continue
            merge_answer(answers, q["year"], keys, [keys[n - 1] for n in nums if n])
            break
    return answers


def cmd_verify(a) -> None:
    from .verify import (CATEGORIES, build_candidates, next_questions, render_results,
                         score_candidates, select_questions, verdict)
    if a.time is None and not a.all_hours:
        a.all_hours = True
    cands = build_candidates(_birth(a), a.tz, a.gender, a.longitude,
                             all_hours=a.all_hours, vary_gender=a.vary_gender)
    by = int(a.date[:4])
    years = list(range(a.from_year or by + 16, (a.to_year or datetime.now().year - 1) + 1))
    questions = select_questions(cands, years, n=a.questions)

    if a.export_questions:
        payload = {"categories": CATEGORIES, "questions": questions,
                   "answer_format": {"<year>": {"asked": ["<category>", "..."], "happened": ["<category>"]}}}
        with open(a.export_questions, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print(f"wrote {a.export_questions}")
        return

    if a.answers:
        with open(a.answers, encoding="utf-8") as fh:
            answers = json.load(fh)
    elif sys.stdin.isatty():
        print(f"Checking {len(cands)} candidate charts:")
        for c in cands:
            print(f"  {c.key}  ({c.label})")
        answers = _ask_interactively(questions, {})
        for rnd in range(a.rounds - 1):
            if not answers or verdict(score_candidates(cands, answers)) == "confident":
                break
            follow = next_questions(cands, years, answers, n=a.followup)
            if not follow:
                break
            print(f"\nNot conclusive yet — {len(follow)} follow-up years to narrow it down:")
            answers = _ask_interactively(follow, answers, show_help=False)
        if a.save_answers and answers:
            with open(a.save_answers, "w", encoding="utf-8") as fh:
                json.dump(answers, fh, ensure_ascii=False, indent=2)
            print(f"saved answers to {a.save_answers}")
    else:
        sys.exit("No --answers file given and stdin is not interactive; "
                 "use --export-questions to get the questionnaire.")
    if not answers:
        sys.exit("No answers given.")
    if a.next_questions:
        print(json.dumps(next_questions(cands, years, answers, n=a.followup), ensure_ascii=False, indent=2))
        return
    _write(render_results(score_candidates(cands, answers)), a.output)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ("chart", "verify", "-h", "--help"):
        argv.insert(0, "chart")  # backwards compatible: bare options mean `chart`

    ap = argparse.ArgumentParser(prog="bazi", description="Four Pillars chart, forecast and verification")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("chart", help="natal chart + yearly/monthly forecast")
    _common(pc)
    pc.add_argument("--zi", choices=["late", "early"], default="late",
                    help="23:00-24:00 handling: late = keep day (晚子时), early = next day (子初换日)")
    pc.add_argument("--year", type=int, action="append",
                    help="forecast year (repeatable); default: current and next year")
    pc.add_argument("-o", "--output", help="write markdown to this file")
    pc.set_defaults(func=cmd_chart)

    pv = sub.add_parser("verify", help="confirm the chart by checking past life events (定盘)")
    _common(pv)
    pv.add_argument("--questions", type=int, default=6, help="number of years to ask about (default 6)")
    pv.add_argument("--from-year", type=int, help="earliest year to consider (default: age 16)")
    pv.add_argument("--to-year", type=int, help="latest year to consider (default: last year)")
    pv.add_argument("--all-hours", action="store_true", help="test all 12 two-hour periods (unknown time)")
    pv.add_argument("--vary-gender", action="store_true", help="also test the other luck direction")
    pv.add_argument("--answers", help="JSON file of answers (skip the interactive prompts)")
    pv.add_argument("--rounds", type=int, default=3, help="max interactive rounds (default 3)")
    pv.add_argument("--followup", type=int, default=4, help="years per follow-up round (default 4)")
    pv.add_argument("--save-answers", help="save interactive answers to this JSON file")
    pv.add_argument("--next-questions", action="store_true",
                    help="with --answers: print follow-up years (JSON) instead of the result")
    pv.add_argument("--export-questions", help="write the questionnaire as JSON and exit")
    pv.add_argument("-o", "--output", help="write the result markdown to this file")
    pv.set_defaults(func=cmd_verify)

    a = ap.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
