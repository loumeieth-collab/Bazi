import json
from datetime import datetime

from bazi.__main__ import main
from bazi.verify import (CATEGORIES, build_candidates, merge_answer, next_questions, score_candidates,
                         select_questions, year_signals)

BIRTH = datetime(1984, 12, 19, 23, 6)


def cands():
    return build_candidates(BIRTH, 8, "M", longitude=101.69)


def test_candidates_are_distinct_and_normalised():
    cs = cands()
    keys = [c.key for c in cs]
    assert len(keys) == len(set(keys))
    assert abs(sum(c.prior for c in cs) - 1) < 1e-9
    assert "甲子 丙子 丁亥 壬子 M" in keys and "甲子 丙子 丁亥 辛亥 M" in keys
    assert "甲子 丙子 戊子 壬子 M" in keys  # 子初换日 variant


def test_all_hours_gives_twelve_hour_pillars():
    cs = build_candidates(BIRTH, 8, "M", all_hours=True)
    assert len({c.chart.pillars["hour"].branch for c in cs}) == 12


def test_signals_reflect_clashes():
    from bazi.chart import Chart
    c = Chart(BIRTH, 8, "M")  # day branch 亥, month branch 子
    assert year_signals(c, 2025)["relationship"] >= 0.5   # 巳 clashes day 亥
    assert year_signals(c, 2014)["career"] >= 0.5         # 午 clashes month 子
    assert all(0 <= v <= 1 for v in year_signals(c, 2014).values())


def test_answers_consistent_with_a_candidate_rank_it_first():
    cs = cands()
    years = list(range(2000, 2026))
    target = next(c for c in cs if c.key.endswith("辛亥 M"))
    # Simulate a person whose life follows the 辛亥 chart's strong signals,
    # answering an initial round plus adaptive follow-up rounds.
    answers = {}

    def answer(qs):
        for q in qs:
            sig = year_signals(target.chart, q["year"])
            merge_answer(answers, q["year"], q["categories"],
                         [k for k in q["categories"] if sig[k] >= 0.5])

    answer(select_questions(cs, years, n=6))
    for _ in range(4):
        answer(next_questions(cs, years, answers, n=4))
    res = score_candidates(cs, answers)
    assert res[0]["candidate"].key == target.key
    assert abs(sum(r["posterior"] for r in res) - 1) < 1e-9


def test_each_candidate_recoverable():
    """Whichever candidate a simulated person 'is', adaptive questioning finds it."""
    cs = cands()
    years = list(range(2000, 2026))
    for target in cs:
        answers = {}
        qs = select_questions(cs, years, n=6)
        for _ in range(6):
            for q in qs:
                sig = year_signals(target.chart, q["year"])
                merge_answer(answers, q["year"], q["categories"],
                             [k for k in q["categories"] if sig[k] >= 0.5])
            qs = next_questions(cs, years, answers, n=4)
        assert score_candidates(cs, answers)[0]["candidate"].key == target.key, target.label


def test_simple_answer_format_and_cli(tmp_path, capsys):
    ans = tmp_path / "a.json"
    ans.write_text(json.dumps({"2014": ["career"], "2025": []}))
    main(["verify", "--date", "1984-12-19", "--time", "23:06", "--gender", "M",
          "--longitude", "101.69", "--answers", str(ans)])
    out = capsys.readouterr().out
    assert "Verification result" in out and "Best match" in out
    q = tmp_path / "q.json"
    main(["verify", "--date", "1984-12-19", "--time", "23:06", "--gender", "M",
          "--export-questions", str(q)])
    data = json.loads(q.read_text())
    assert len(data["questions"]) == 6 and set(data["categories"]) == set(CATEGORIES)


def test_legacy_cli_still_works(capsys):
    main(["--date", "1984-12-19", "--time", "23:06", "--gender", "M", "--year", "2027"])
    assert "2027 丁未" in capsys.readouterr().out


def test_remembered_events_cli(capsys):
    main(["verify", "--date", "1984-12-19", "--time", "23:06", "--gender", "M", "--longitude", "101.69",
          "--event", "2013:relocation,health", "--event", "2025:relocation", "--event", "2016:none"])
    out = capsys.readouterr().out
    # These events hinge on the 丁亥 day branch (巳亥 clash), so the 戊子-day
    # candidates must drop out while the hour candidates stay in contention.
    best = out.split("Best match")[1]
    assert "丁亥" in best
    assert "| 0% | 甲子 丙子 戊子" in out


def test_spouse_palace_frame_and_combined_spouse_star():
    from bazi.chart import Chart
    c = Chart(BIRTH, 8, "M", longitude=101.69)  # 丁亥 day; 2021 辛丑 completes 亥子丑
    assert year_signals(c, 2021)["relationship"] >= 0.7
    assert year_signals(c, 2011)["relationship"] >= 0.7  # 卯亥 half-combo + 辛 偏财


def test_decade_and_year_quality():
    from bazi.chart import Chart
    from bazi.verify import decade_probability
    d = Chart(BIRTH, 8, "M", longitude=101.69)   # 丁: 己卯 decade good, 庚辰 hard
    w = Chart(BIRTH, 8, "M", zi_mode="early")    # 戊: both decades hard
    assert decade_probability(d, 2010, 2020, "worse") > decade_probability(w, 2010, 2020, "worse")
    for c in (d, w):
        assert abs(sum(decade_probability(c, 2010, 2020, r) for r in ("better", "same", "worse")) - 1) < 0.2
    assert year_signals(w, 2009)["good_year"] > year_signals(d, 2009)["good_year"]


def test_fixed_hour_pillar_keeps_both_day_conventions():
    cs = build_candidates(BIRTH, 8, "M", longitude=101.69, hour_pillar="壬子")
    assert {c.chart.day_master for c in cs} == {"丁", "戊"}
    assert all(str(c.chart.pillars["hour"]) == "壬子" for c in cs)
