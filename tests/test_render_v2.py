"""
Test 3 (renderer totality) for the DRAFT v2 arm-2 prompt (register A74), plus checks that v2
differs from frozen v1 only where A74 says it does.
"""
import dataclasses
import pathlib
import string

import pytest

import render_v2 as r2
import step4_prompt_tokens as r1
from perception import Perception, PerceptionV2

ROOT = pathlib.Path(__file__).resolve().parents[1]
V1 = ROOT / "prompts" / "frozen_v1"
V2 = ROOT / "prompts" / "v2"

BASE = dict(deaths_cumulative=40.6, current_action="precautions", social_norm=0.734,
            age_band=7, vulnerability=0.0193, occupation_flex=0.62, response_efficacy=0.41,
            population=15000, day=45)
# One alternative value per field, chosen so its rendered text differs from BASE's.
ALT = dict(deaths_7day_mean=2.0, deaths_7day_mean_7d_ago=0.9, deaths_cumulative=55.0,
           current_action="stay_home", social_norm=0.5, age_band=2, vulnerability=0.0004,
           occupation_flex=0.1, response_efficacy=0.9, population=10000, day=46)


def _p2(**kw):
    return PerceptionV2(**{**BASE, "deaths_7day_mean": 1.3, "deaths_7day_mean_7d_ago": 0.4, **kw})


def _placeholders(template):
    return [f for _, f, _, _ in string.Formatter().parse(template) if f is not None]


def test_template_v2_is_byte_identical_to_v1():
    assert (V2 / "arm2_template_v2.txt").read_bytes() == (V1 / "arm2_template_v1.txt").read_bytes()


def test_every_field_has_exactly_one_placeholder_and_each_occurs_once():
    fields = {f.name for f in dataclasses.fields(PerceptionV2)}
    assert set(r2.FIELD_PLACEHOLDER) == fields
    assert len(set(r2.FIELD_PLACEHOLDER.values())) == len(fields)
    ph = _placeholders(r2.TEMPLATE)
    assert sorted(ph) == sorted(r2.FIELD_PLACEHOLDER.values())   # each exactly once


@pytest.mark.parametrize("field", sorted(ALT))
def test_changing_one_field_changes_only_its_placeholder_line(field):
    base, alt = r2.render(_p2()), r2.render(_p2(**{field: ALT[field]}))
    changed = [i for i, (a, b) in enumerate(zip(base.split("\n"), alt.split("\n"))) if a != b]
    lines = r2.TEMPLATE.split("\n")
    expect = [i for i, line in enumerate(lines) if "{" + r2.FIELD_PLACEHOLDER[field] + "}" in line]
    assert changed == expect
    if field == "day":   # day also drives the death-sentence wording; 45 -> 46 keeps both forms
        assert base.split("\n")[2] == alt.split("\n")[2]


def test_no_placeholder_left_unfilled():
    text = r2.render(_p2())
    assert "{" not in text and "}" not in text


def test_v1_helpers_unchanged():
    assert r2.AGE_TEXT == r1.AGE_TEXT and r2.ACTION_TEXT == r1.ACTION_TEXT
    for v in (0.0, 0.00004, 0.0004, 0.004, 0.0193, 0.08, 0.3):
        assert r2.natural_frequency(v) == r1.natural_frequency(v)
    for x in (0.0, 0.49, 0.5, 1.5, 2.5, 7.49):
        assert r2.half_up(x) == r1.half_up(x)


@pytest.mark.parametrize("day", [0, 3, 6, 7, 10, 13, 14, 27, 28, 34, 35, 45, 300])
def test_v2_differs_from_v1_only_in_the_deaths_line(day):
    p2 = _p2(day=day)
    p1 = Perception(**{**BASE, "day": day, "deaths_28day_mean": 1.3, "deaths_28day_mean_7d_ago": 0.4})
    a, b = r1.render(p1).split("\n"), r2.render(p2).split("\n")
    assert len(a) == len(b)
    assert [i for i in range(len(a)) if a[i] != b[i]] in ([], [2])
    assert b[2].endswith(f" In total, {r2.half_up(BASE['deaths_cumulative'])} people in your town have died of it so far.")


@pytest.mark.parametrize("day,recent,earlier", [
    (0, "Since the outbreak began, 0 people in your town have died of it.", "A week ago, 0 people had died of it."),
    (6, "Since the outbreak began, 8 people in your town have died of it.", "A week ago, 0 people had died of it."),
    (7, "In the past week, 9 people in your town died of it.",
     "Between the start of the outbreak and a week ago, 0 died."),
    (10, "In the past week, 9 people in your town died of it.",
     "Between the start of the outbreak and a week ago, 1 died."),
    (14, "In the past week, 9 people in your town died of it.", "In the week before that, 3 died."),
    (45, "In the past week, 9 people in your town died of it.", "In the week before that, 3 died."),
])
def test_death_sentences_follow_a74(day, recent, earlier):
    # deaths_7day_mean 1.3 -> n = half_up(min(7, day) * 1.3); 7d_ago 0.4 -> m = half_up(min(7, day - 7) * 0.4)
    assert r2.death_sentences(day, 1.3, 0.4) == (recent, earlier)


def test_arm3_instruction_v2_is_v1_with_the_two_attribute_lines_replaced():
    import step13_v2_smoke as s13
    a = (V1 / "arm3_instruction_v1.txt").read_text(encoding="utf-8")
    b = (V2 / "arm3_instruction_v2.txt").read_text(encoding="utf-8")
    assert a.count(s13.ARM3_V1_LINES) == 1
    assert b == a.replace(s13.ARM3_V1_LINES, s13.ARM3_V2_LINES)
    assert "deaths_28day" not in b and "min(28" not in b
    assert r2.TEMPLATE in b          # the embedded template is the v2 template, verbatim
