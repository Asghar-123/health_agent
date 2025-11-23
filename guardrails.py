from pydantic import BaseModel, validator
from typing import Optional, Set
import re


class ParsedGoal(BaseModel):
    """
    A Pydantic model representing a parsed health goal.
    """
    target: str
    quantity: float
    unit: str
    duration_value: int
    duration_unit: str

    @validator('target')
    def target_allowed(cls, v: str) -> str:
        """
        Validator to ensure the target is one of the allowed actions.
        """
        allowed: Set[str] = {'lose', 'gain', 'increase', 'decrease', 'run', 'walk'}
        if v.lower() not in allowed:
            raise ValueError(f'Unsupported target {v}. Use one of {allowed}')
        return v.lower()

    @validator('unit')
    def unit_allowed(cls, v: str) -> str:
        """
        Validator to ensure the unit is one of the allowed units.
        """
        allowed: Set[str] = {'kg', 'lbs', 'km', 'miles', 'minutes', 'min', 'percent', '%', 'calories', 'steps'}
        if v.lower() not in allowed:
            raise ValueError(f'Unsupported unit {v}. Use one of {allowed}')
        return v.lower()


def parse_goal_text(text: str) -> Optional[ParsedGoal]:
    """
    Parses a natural language text to extract a health goal.

    Args:
        text: The input text to parse.

    Returns:
        A ParsedGoal object if a goal is found, otherwise None.
    """
    # Regex to capture goals like: 'lose 5kg in 2 months', 'run 10km in 1 week', etc.
    m = re.search(
        r"(lose|gain|increase|decrease|run|walk)\s+(\d+(?:\.\d+)?)\s*([a-zA-Z%]+)\s+(in|within)\s+(\d+)\s*([a-zA-Z]+)",
        text, re.I
    )
    if not m:
        return None

    action, quantity, unit, _, duration_value, duration_unit = (
        m.group(1),
        float(m.group(2)),
        m.group(3),
        m.group(4),
        int(m.group(5)),
        m.group(6)
    )

    return ParsedGoal(
        target=action,
        quantity=quantity,
        unit=unit,
        duration_value=duration_value,
        duration_unit=duration_unit
    )