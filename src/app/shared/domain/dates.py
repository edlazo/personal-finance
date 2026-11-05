"""Aritmética de fechas compartida por los módulos."""

from calendar import monthrange
from datetime import date


def add_months(start: date, months: int) -> date:
    """El mismo día N meses después o, si el mes es más corto, su último día."""
    year, index = divmod(start.year * 12 + start.month - 1 + months, 12)
    return date(year, index + 1, min(start.day, monthrange(year, index + 1)[1]))
