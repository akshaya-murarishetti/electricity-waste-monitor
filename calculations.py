"""
Core calculation functions for Electricity Waste Monitor.
All results are estimates based on user-entered data unless source is a device reading.
"""


def daily_energy_kwh(power_watts, quantity, hours_per_day):
    """
    Daily Energy (kWh) = Power (W) × Quantity × Hours used per day ÷ 1000
    """
    power = float(power_watts)
    qty = float(quantity)
    hours = float(hours_per_day)
    if power < 0 or qty <= 0 or hours < 0 or hours > 24:
        raise ValueError("Invalid input for energy calculation")
    return round(power * qty * hours / 1000.0, 4)


def monthly_energy_kwh(daily_kwh, days=30):
    """Estimated monthly energy = daily energy × number of days."""
    return round(float(daily_kwh) * int(days), 4)


def estimated_cost(energy_kwh, tariff_per_kwh):
    """Estimated cost = energy (kWh) × tariff per kWh."""
    return round(float(energy_kwh) * float(tariff_per_kwh), 2)


def calculate_appliance_consumption(power_watts, quantity, hours_per_day, tariff_per_kwh, days=30):
    """
    Full calculation for one appliance (or group of identical appliances).
    Returns a dict with daily/monthly energy and costs.
    """
    daily = daily_energy_kwh(power_watts, quantity, hours_per_day)
    monthly = monthly_energy_kwh(daily, days)
    daily_cost = estimated_cost(daily, tariff_per_kwh)
    monthly_cost = estimated_cost(monthly, tariff_per_kwh)
    return {
        "daily_kwh": daily,
        "monthly_kwh": monthly,
        "daily_cost": daily_cost,
        "monthly_cost": monthly_cost,
        "tariff": float(tariff_per_kwh),
        "days": int(days),
        "is_estimate": True,
    }


def total_from_appliances(appliances, tariff_per_kwh, days=30):
    """
    Sum consumption across a list of appliance dicts.
    Each appliance must have: power_watts, quantity, hours_per_day.
    """
    total_daily = 0.0
    details = []
    for app in appliances:
        result = calculate_appliance_consumption(
            app["power_watts"],
            app["quantity"],
            app["hours_per_day"],
            tariff_per_kwh,
            days,
        )
        result["name"] = app.get("name", "Appliance")
        result["category"] = app.get("category")
        details.append(result)
        total_daily += result["daily_kwh"]

    total_monthly = monthly_energy_kwh(total_daily, days)
    return {
        "daily_kwh": round(total_daily, 4),
        "monthly_kwh": total_monthly,
        "daily_cost": estimated_cost(total_daily, tariff_per_kwh),
        "monthly_cost": estimated_cost(total_monthly, tariff_per_kwh),
        "tariff": float(tariff_per_kwh),
        "days": int(days),
        "appliance_details": details,
        "is_estimate": True,
    }


def validate_appliance_input(name, power_watts, quantity, hours_per_day):
    """
    Validate appliance form input. Returns (ok: bool, errors: list[str]).
    """
    errors = []
    if not name or not str(name).strip():
        errors.append("Appliance name is required.")
    try:
        pw = float(power_watts)
        if pw < 0:
            errors.append("Power rating cannot be negative.")
    except (TypeError, ValueError):
        errors.append("Power rating must be a valid number.")

    try:
        qty = int(quantity)
        if qty <= 0:
            errors.append("Quantity must be a positive integer.")
    except (TypeError, ValueError):
        errors.append("Quantity must be a positive integer.")

    try:
        hrs = float(hours_per_day)
        if hrs < 0 or hrs > 24:
            errors.append("Usage hours must be between 0 and 24 per day.")
    except (TypeError, ValueError):
        errors.append("Usage hours must be a valid number between 0 and 24.")

    return len(errors) == 0, errors


def validate_tariff(tariff):
    try:
        t = float(tariff)
        if t < 0:
            return False, "Tariff cannot be negative."
        return True, None
    except (TypeError, ValueError):
        return False, "Tariff must be a valid number."


def validate_energy(energy_kwh):
    try:
        e = float(energy_kwh)
        if e < 0:
            return False, "Consumption cannot be negative."
        return True, None
    except (TypeError, ValueError):
        return False, "Consumption must be a valid number."
