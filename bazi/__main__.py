"""Command line: python -m bazi --date 1990-05-01 --time 14:30 --gender F --year 2027"""
from __future__ import annotations

import argparse
from datetime import datetime

from .chart import Chart
from .report import full_report


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bazi", description="Four Pillars chart & yearly forecast")
    ap.add_argument("--date", required=True, help="birth date YYYY-MM-DD (Gregorian)")
    ap.add_argument("--time", default=None, help="birth clock time HH:MM (omit if unknown)")
    ap.add_argument("--gender", required=True, choices=["M", "F", "m", "f"])
    ap.add_argument("--tz", type=float, default=8.0, help="UTC offset in hours at birth (default 8)")
    ap.add_argument("--longitude", type=float, default=None,
                    help="birthplace longitude (°E) to use true solar time for the hour")
    ap.add_argument("--zi", choices=["late", "early"], default="late",
                    help="23:00-24:00 handling: late = keep day (晚子时), early = next day (子初换日)")
    ap.add_argument("--year", type=int, action="append",
                    help="forecast year (repeatable); default: current and next year")
    ap.add_argument("-o", "--output", help="write markdown to this file")
    a = ap.parse_args(argv)

    t = a.time or "12:00"
    birth = datetime.strptime(f"{a.date} {t}", "%Y-%m-%d %H:%M")
    c = Chart(birth, a.tz, a.gender, longitude=a.longitude, zi_mode=a.zi, hour_known=a.time is not None)
    years = a.year or [datetime.now().year, datetime.now().year + 1]
    md = full_report(c, years)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"wrote {a.output}")
    else:
        print(md)


if __name__ == "__main__":
    main()
