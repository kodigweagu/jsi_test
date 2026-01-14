"""Tests for CSV parsing utilities."""

import pytest

from app.csvparser import parse_datetime


def test_parse_datetime_rejects_invalid_value():
    """Raise ValueError on unsupported formats."""
    with pytest.raises(ValueError):
        parse_datetime("not-a-date")
