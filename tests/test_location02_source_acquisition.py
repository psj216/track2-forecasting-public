"""Executive summary: the release universe must come from dated official archive entries."""
import pytest
from backtesting.location02.source_acquisition import enumerate_archive


def entry(date, year=2020, quarter=2):
    return f'<dl><dt>{date}</dt><dd><div class="title"><a href="/stats/ecb_surveys/survey_of_professional_forecasters/pdf/ecb.spf{year}q{quarter}.en.pdf">SPF</a></div><a class="pdf" href="/stats/ecb_surveys/survey_of_professional_forecasters/pdf/ecb.spf{year}q{quarter}.en.pdf">English</a></dd></dl>'


def test_actual_publication_date_not_assumed_quarter_date():
    row = enumerate_archive(entry("4 May 2020"))[0]
    assert row["publication_date"] == "2020-05-04"
    assert row["round_id"] == "2020Q2"


def test_duplicate_round_blocks_universe():
    with pytest.raises(ValueError, match="Duplicate"):
        enumerate_archive(entry("4 May 2020") + entry("4 May 2020"))


def test_future_round_and_special_questionnaire_are_excluded():
    body = entry("24 July 2026", 2026, 3) + entry("23 January 2015", 2015, 1)
    assert [row["round_id"] for row in enumerate_archive(body)] == ["2015Q1"]


def test_absent_archive_date_blocks_universe():
    with pytest.raises(ValueError):
        enumerate_archive(entry("4 May 2020").replace("<dt>4 May 2020</dt>", ""))
