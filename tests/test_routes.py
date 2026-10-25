"""Basic route and API tests using Flask test client."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app import app
import database as db


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Use a temporary database for tests."""
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", test_db)
    db.init_db()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_dashboard_loads(client):
    rv = client.get("/")
    assert rv.status_code == 200
    assert b"Dashboard" in rv.data or b"Est." in rv.data


def test_appliances_page(client):
    rv = client.get("/appliances")
    assert rv.status_code == 200


def test_add_appliance(client):
    rv = client.post(
        "/appliances",
        data={
            "action": "add",
            "name": "Test Fan",
            "power_watts": "75",
            "quantity": "1",
            "hours_per_day": "12",
            "category": "Cooling",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert b"Test Fan" in rv.data


def test_calculator_fan_example(client):
    rv = client.post(
        "/calculator",
        data={
            "name": "Fan",
            "power_watts": "75",
            "quantity": "1",
            "hours_per_day": "12",
            "tariff": "8",
            "days": "30",
        },
    )
    assert rv.status_code == 200
    assert b"0.900" in rv.data or b"0.9" in rv.data
    assert b"27" in rv.data
    assert b"216" in rv.data


def test_negative_power_on_calculator(client):
    rv = client.post(
        "/calculator",
        data={
            "name": "Bad",
            "power_watts": "-5",
            "quantity": "1",
            "hours_per_day": "5",
            "tariff": "8",
            "days": "30",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert b"negative" in rv.data.lower() or b"danger" in rv.data


def test_api_dashboard(client):
    rv = client.get("/api/dashboard")
    assert rv.status_code == 200
    data = rv.get_json()
    assert "estimated_daily_kwh" in data
    assert data["device_connected"] is False


def test_device_status_disconnected(client):
    rv = client.get("/device")
    assert rv.status_code == 200
    assert b"not connected" in rv.data.lower() or b"Device not connected" in rv.data


def test_api_device_reading(client):
    rv = client.post(
        "/api/device-readings",
        json={
            "device_id": "test-meter",
            "timestamp": "2026-10-25T12:00:00",
            "energy_kwh": 2.5,
            "power_watts": 400,
        },
    )
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["ok"] is True

    rv2 = client.get("/device")
    assert b"test-meter" in rv2.data or b"readings received" in rv2.data.lower()
