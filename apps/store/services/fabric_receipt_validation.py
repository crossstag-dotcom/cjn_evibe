"""Pure validation and reconciliation rules for supplier fabric delivery challans.

No stock is posted by this module. Persistence and approval are separate steps.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation


class FabricReceiptError(ValueError):
    """A delivery challan cannot be confirmed as entered."""


def normalize_roll_number(value):
    """Preserve printed roll IDs, including leading zeros."""
    if value is None:
        raise FabricReceiptError("Roll number is required.")
    number = str(value).strip()
    if not number:
        raise FabricReceiptError("Roll number is required.")
    return number


def normalize_meters(value):
    """Accept positive meter quantities without floating-point rounding."""
    try:
        meters = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise FabricReceiptError("Roll meters must be a valid number.") from None
    if not meters.is_finite() or meters <= 0:
        raise FabricReceiptError("Roll meters must be greater than zero.")
    return meters


def validate_dc_rolls(rolls):
    """Validate draft lines and return grouped quantities and total meters.

    Each item is a mapping with fabric_code, roll_number, and meters.
    The same printed roll number may need supplier-specific interpretation,
    but must not appear twice within a single DC.
    """
    if not rolls:
        raise FabricReceiptError("At least one roll is required.")
    seen = set()
    groups = {}
    for index, item in enumerate(rolls, start=1):
        fabric = str(item.get("fabric_code") or "").strip()
        if not fabric:
            raise FabricReceiptError(f"Roll {index}: fabric description is required.")
        number = normalize_roll_number(item.get("roll_number"))
        if number in seen:
            raise FabricReceiptError(f"Duplicate roll number in DC: {number}")
        seen.add(number)
        meters = normalize_meters(item.get("meters"))
        group = groups.setdefault(fabric, {"roll_count": 0, "meters": Decimal("0")})
        group["roll_count"] += 1
        group["meters"] += meters
    return {
        "roll_count": len(rolls),
        "total_meters": sum((group["meters"] for group in groups.values()), Decimal("0")),
        "fabrics": groups,
    }
