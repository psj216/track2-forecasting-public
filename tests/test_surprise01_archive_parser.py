"""## Executive summary (read this first)

Archive parsing distinguishes monthly first estimates from annual/revised figures.
These are synthetic release snippets, not market outcome fixtures.
"""
from backtesting.surprise01.build_event_ledger import cpi_values, employment_values, ip_value, retail_value


def test_fixed_width_cpi():
    text = 'Table A. Compound annual rate All Items .1 .2 .3 .4 .5 .6 .7 4.5 3.2 All items less food & energy .0 .1 .2 .3 .4 .5 .6 3.4 2.1 '
    assert cpi_values(text, None) == {'CPI': .7, 'Core CPI': .6}


def test_qualitative_payroll_numeric_table():
    text = 'THE EMPLOYMENT SITUATION: MAY 2001 The unemployment rate was 4.4 percent. Nonfarm employment.......| 132,000|p132,009| p-19 Goods-producing'
    assert employment_values(text) == {'Payrolls': -19., 'Unemployment': 4.4}


def test_first_ip_monthly_not_revision():
    assert ip_value('In July, total industrial production increased 0.6 percent. June was revised to 0.9 percent.') == .6
    assert ip_value('Industrial production fell back 0.4 percent in September.') == -.4
    assert ip_value('Industrial production was little changed in April. Total index 100 101 102 103 .1 .2 .3 .1 -.4 Previous estimates') == .1


def test_retail_advance_not_revision():
    text = 'Advance estimates of U.S. retail and food services sales were up 0.4 percent from the previous month. Prior month revised to up 0.8 percent.'
    assert retail_value(text) == .4
