import re
from datetime import datetime, timezone

import pytest

from pymdtools.common import today_utc, now_utc_timestamp, parse_timestamp


def test_today_utc_format():
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", today_utc())


def test_now_utc_timestamp_format():
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", now_utc_timestamp())


def test_parse_timestamp_iso_naive():
    dt = parse_timestamp("2026-02-01 12:34:56")
    assert isinstance(dt, datetime)
    assert dt.year == 2026
    assert dt.tzinfo is None


def test_parse_timestamp_iso_with_timezone():
    dt = parse_timestamp("2026-02-01T12:34:56+01:00")
    assert dt.tzinfo is not None
