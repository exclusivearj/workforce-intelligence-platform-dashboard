"""Tests for the filter sidebar pure logic."""

from __future__ import annotations

from src.components.filters import default_filters, normalize_filters


def test_default_filters_shape():
    d = default_filters()
    assert d["departments"] == []
    assert d["employment_type"] is None
    assert d["start_date"] < d["end_date"]


def test_normalize_collapses_all():
    out = normalize_filters(
        {"departments": ["All", "Data"], "levels": ["All"], "employment_type": "All"}
    )
    assert out["departments"] == ["Data"]
    assert out["levels"] == []
    assert out["employment_type"] is None


def test_normalize_maps_employment_type():
    assert normalize_filters({"employment_type": "Full-time"})["employment_type"] == "full_time"
    assert normalize_filters({"employment_type": "Contractor"})["employment_type"] == "contractor"


def test_normalize_defaults_dates_when_missing():
    out = normalize_filters({})
    assert out["start_date"]
    assert out["end_date"]
