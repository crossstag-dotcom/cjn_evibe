"""Pure planning checks; does not issue rolls or deduct fabric."""
from decimal import Decimal, InvalidOperation


class CuttingPlanError(ValueError):
    pass


def summarize_cutting_plan(size_quantities, average_meters, roll_meters):
    if not size_quantities:
        raise CuttingPlanError("Enter at least one size.")
    if any(isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0 for qty in size_quantities.values()):
        raise CuttingPlanError("Each size quantity must be a positive whole number.")
    try:
        average = Decimal(str(average_meters))
        available = Decimal(str(roll_meters))
    except (InvalidOperation, ValueError, TypeError):
        raise CuttingPlanError("Average and roll meters must be valid numbers.") from None
    if not average.is_finite() or not available.is_finite() or average <= 0 or available <= 0:
        raise CuttingPlanError("Average and roll meters must be positive finite numbers.")
    pieces = sum(size_quantities.values())
    estimated = average * pieces
    return {
        "planned_pieces": pieces,
        "estimated_meters": estimated,
        "roll_meters": available,
        "estimated_difference_meters": available - estimated,
        "estimated_exceeds_roll": estimated > available,
    }
