import random
from datetime import datetime, timedelta

import pytest

from bazi import astro
from bazi.chart import Chart, Pillar, day_pillar_for_date, ten_god
from bazi.forecast import annual_forecast

lunar = pytest.importorskip("lunar_python")


def ref(dt):
    e = lunar.Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0).getLunar().getEightChar()
    e.setSect(2)  # 晚子时 keeps the day
    return [e.getYear(), e.getMonth(), e.getDay(), e.getTime()]


def ours(dt):
    c = Chart(dt, 8, "M")
    return [str(c.pillars[k]) for k in ("year", "month", "day", "hour")]


def test_known_dates():
    assert str(day_pillar_for_date(2000, 1, 1)) == "戊午"
    assert ours(datetime(1984, 12, 19, 23, 6)) == ["甲子", "丙子", "丁亥", "壬子"]


def test_random_charts_match_reference():
    rng = random.Random(42)
    mismatches = []
    for _ in range(3000):
        dt = datetime(1920, 1, 1) + timedelta(minutes=rng.randrange(0, 60 * 24 * 365 * 110))
        if ours(dt) != ref(dt):
            mismatches.append((dt, ours(dt), ref(dt)))
    # Differences may only occur within minutes of a solar term
    for dt, o, r in mismatches:
        lon = astro.sun_longitude(astro.julian_day(dt - timedelta(hours=8)))
        assert min(abs((lon - 15) % 30), 30 - abs((lon - 15) % 30)) < 0.01, (dt, o, r)


def test_solar_terms_within_minutes():
    for year in (1950, 1984, 2000, 2026, 2040):
        tbl = lunar.Solar.fromYmd(year, 6, 1).getLunar().getJieQiTable()
        for name, lon in (("立春", 315), ("夏至", 90), ("立秋", 135), ("冬至", 270)):
            t = tbl[name]
            ref_dt = datetime(t.getYear(), t.getMonth(), t.getDay(), t.getHour(), t.getMinute(), t.getSecond())
            jd = astro.solar_term_jd(ref_dt.year, lon)
            mine = astro.from_julian_day(jd) + timedelta(hours=8)
            assert abs((mine - ref_dt).total_seconds()) < 600, (year, name, mine, ref_dt)


def test_ten_gods():
    assert ten_god("丁", "壬") == "正官"
    assert ten_god("丁", "癸") == "七杀"
    assert ten_god("丁", "甲") == "正印"
    assert ten_god("丁", "丙") == "劫财"
    assert ten_god("甲", "己") == "正财"


def test_luck_pillars_match_reference():
    for g, gi in (("M", 1), ("F", 0)):
        c = Chart(datetime(1984, 12, 19, 23, 6), 8, g)
        e = lunar.Solar.fromYmdHms(1984, 12, 19, 23, 6, 0).getLunar().getEightChar()
        e.setSect(2)
        expect = [d.getGanZhi() for d in e.getYun(gi).getDaYun()[1:9]]
        assert [str(lp["pillar"]) for lp in c.luck_pillars(8)] == expect


def test_true_solar_time_and_zi_modes():
    c = Chart(datetime(1984, 12, 19, 23, 6), 8, "M", longitude=100.33)
    assert str(c.pillars["hour"]) == "辛亥"
    c = Chart(datetime(1984, 12, 19, 23, 6), 8, "M", zi_mode="early")
    assert str(c.pillars["day"]) == "戊子" and str(c.pillars["hour"]) == "壬子"


def test_annual_forecast_structure():
    c = Chart(datetime(1984, 12, 19, 23, 6), 8, "M")
    f = annual_forecast(c, 2027)
    assert str(f["pillar"]) == "丁未"
    assert [str(m.pillar) for m in f["months"]][:3] == ["壬寅", "癸卯", "甲辰"]
    assert f["months"][0].start.month == 2
    assert len(f["months"]) == 12
