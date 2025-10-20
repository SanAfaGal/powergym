from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class SubscriptionCalculator:
    """Subscription date calculations"""

    @staticmethod
    def calculate_end_date(start_date: date, plan) -> date:
        """
        Calculate end_date based on plan duration.

        Plan attributes:
        - duration_count: number (e.g., 1, 3, 12)
        - duration_unit: "day" | "week" | "month" | "year"

        Returns: end_date (the last day of the subscription)
        """
        duration_unit = (
            plan.duration_unit.value
            if hasattr(plan.duration_unit, 'value')
            else plan.duration_unit
        )

        if duration_unit == "day":
            end_date = start_date + timedelta(days=plan.duration_count)
        elif duration_unit == "week":
            end_date = start_date + timedelta(weeks=plan.duration_count)
        elif duration_unit == "month":
            end_date = start_date + relativedelta(months=plan.duration_count)
        elif duration_unit == "year":
            end_date = start_date + relativedelta(years=plan.duration_count)
        else:
            raise ValueError(f"Invalid duration unit: {duration_unit}")

        # Last day is 1 day before the next subscription starts
        return end_date - timedelta(days=1)
