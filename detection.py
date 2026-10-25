"""
Rule-based high-usage detection for Electricity Waste Monitor.
Does not claim confirmed wastage — only flags unusually high values.
"""

from database import (
    get_high_usage_threshold,
    get_threshold_multiplier,
    get_historical_average,
    add_alert,
)


def check_high_usage(energy_kwh, record_date=None, record_id=None, create_alert=True):
    """
    Compare a consumption value against:
    1. User-configured absolute threshold (kWh/day)
    2. Historical average × multiplier (when enough records exist)

    Returns a dict describing whether an alert was raised and why.
    """
    energy = float(energy_kwh)
    threshold = get_high_usage_threshold()
    multiplier = get_threshold_multiplier()
    avg, count = get_historical_average(exclude_date=record_date)

    reasons = []
    triggered = False
    comparison_value = None
    rule_used = None

    if energy > threshold:
        triggered = True
        reasons.append(
            f"Estimated consumption ({energy:.2f} kWh) exceeds the configured "
            f"threshold of {threshold:.2f} kWh."
        )
        comparison_value = threshold
        rule_used = "absolute_threshold"

    if avg is not None and count >= 3:
        baseline = avg * multiplier
        if energy > baseline:
            triggered = True
            reasons.append(
                f"Estimated consumption ({energy:.2f} kWh) is more than "
                f"{multiplier:.1f}\u00d7 the historical average of {avg:.2f} kWh "
                f"(based on {count} previous records)."
            )
            if comparison_value is None or baseline < comparison_value:
                comparison_value = baseline
            rule_used = rule_used or "historical_baseline"

    result = {
        "triggered": triggered,
        "energy_kwh": energy,
        "threshold": threshold,
        "historical_avg": avg,
        "historical_count": count,
        "comparison_value": comparison_value,
        "rule_used": rule_used,
        "reasons": reasons,
        "message": None,
        "suggestion": None,
        "alert_id": None,
    }

    if triggered:
        reason_text = " ".join(reasons)
        message = (
            "Possible high electricity usage detected. "
            + reason_text
            + " This is based on the data entered and configured rules; "
            "it does not prove that energy was wasted."
        )
        suggestion = (
            "Review appliance usage hours, verify the entered data, "
            "and consider switching off unused appliances. "
            "Compare with previous records if available."
        )
        result["message"] = message
        result["suggestion"] = suggestion

        if create_alert:
            alert_id = add_alert(
                alert_type="possible_high_usage",
                message=message,
                threshold_value=comparison_value,
                record_id=record_id,
            )
            result["alert_id"] = alert_id

    return result


def generate_recommendations(appliances, recent_records, active_alerts):
    """
    Produce practical energy-saving recommendations based on available data.
    Recommendations are contextual, not absolute claims of savings.
    """
    recommendations = []

    for app in appliances:
        hours = float(app.get("hours_per_day") or 0)
        power = float(app.get("power_watts") or 0)
        if hours >= 16 and power > 0:
            recommendations.append(
                {
                    "type": "long_usage",
                    "title": f"Review long daily usage: {app['name']}",
                    "text": (
                        f"{app['name']} is set to run about {hours:.1f} hours/day "
                        f"({power:.0f} W). Confirm this matches real usage and "
                        "consider reducing hours if possible."
                    ),
                }
            )
        if power >= 1000 and hours >= 4:
            recommendations.append(
                {
                    "type": "high_power",
                    "title": f"High-power appliance: {app['name']}",
                    "text": (
                        f"{app['name']} draws {power:.0f} W. Using it efficiently "
                        "and avoiding unnecessary runtime can help lower estimated consumption."
                    ),
                }
            )

    if active_alerts:
        recommendations.append(
            {
                "type": "alert_review",
                "title": "Review possible high-usage alerts",
                "text": (
                    f"There are {len(active_alerts)} active alert(s). "
                    "Check the recorded values against your usual pattern and "
                    "verify appliance hours and power ratings."
                ),
            }
        )

    if recent_records and len(recent_records) >= 2:
        latest = recent_records[0]
        prev = recent_records[1]
        if float(latest["energy_kwh"]) > float(prev["energy_kwh"]) * 1.3:
            recommendations.append(
                {
                    "type": "trend",
                    "title": "Recent consumption is higher than previous record",
                    "text": (
                        f"Latest record ({latest['energy_kwh']:.2f} kWh) is noticeably "
                        f"higher than the previous one ({prev['energy_kwh']:.2f} kWh). "
                        "Review what changed in appliance usage."
                    ),
                }
            )

    if not recommendations:
        recommendations.append(
            {
                "type": "general",
                "title": "Switch off unused appliances",
                "text": (
                    "Turn off lights, fans, and other devices when not needed. "
                    "Small daily reductions add up over a billing period."
                ),
            }
        )
        recommendations.append(
            {
                "type": "general",
                "title": "Verify entered data",
                "text": (
                    "Estimates depend on accurate power ratings and usage hours. "
                    "Update appliance details if they do not match real usage."
                ),
            }
        )
        recommendations.append(
            {
                "type": "general",
                "title": "Consider efficient replacements",
                "text": (
                    "When replacing old equipment, look for higher energy-efficiency ratings. "
                    "This is a long-term option, not an immediate saving guarantee."
                ),
            }
        )

    return recommendations
