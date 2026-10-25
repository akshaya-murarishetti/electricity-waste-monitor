"""Unit tests for core calculation formulas."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from calculations import (
    daily_energy_kwh,
    monthly_energy_kwh,
    estimated_cost,
    calculate_appliance_consumption,
    validate_appliance_input,
)


def test_fan_example_daily():
    """75 W × 1 × 12 h ÷ 1000 = 0.9 kWh"""
    assert daily_energy_kwh(75, 1, 12) == 0.9


def test_monthly_from_daily():
    assert monthly_energy_kwh(0.9, 30) == 27.0


def test_cost_example():
    """27 kWh × ₹8 = ₹216"""
    assert estimated_cost(27, 8) == 216.0


def test_full_calculation():
    result = calculate_appliance_consumption(75, 1, 12, 8, 30)
    assert result["daily_kwh"] == 0.9
    assert result["monthly_kwh"] == 27.0
    assert result["monthly_cost"] == 216.0
    assert result["is_estimate"] is True


def test_negative_power_rejected():
    ok, errors = validate_appliance_input("Fan", -10, 1, 5)
    assert ok is False
    assert any("negative" in e.lower() for e in errors)


def test_hours_over_24_rejected():
    ok, errors = validate_appliance_input("Fan", 75, 1, 25)
    assert ok is False
    assert any("24" in e for e in errors)


def test_valid_input_accepted():
    ok, errors = validate_appliance_input("Fan", 75, 1, 12)
    assert ok is True
    assert errors == []
