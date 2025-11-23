from typing import Any, Dict
from guardrails import parse_goal_text


class GoalAnalyzerTool:
    """
    A tool for analyzing and parsing health goals from raw text.
    """
    name = "GoalAnalyzerTool"

    async def run(self, raw_text: str) -> Dict[str, Any]:
        """
        Parses a health goal from raw text.

        Args:
            raw_text: The raw text containing the health goal.

        Returns:
            A dictionary containing the parsed goal information or an error message.
        """
        parsed = parse_goal_text(raw_text)
        if not parsed:
            return {"ok": False, "error": "Could not parse the goal. Please state your goal clearly."}

        structured = {
            "ok": True,
            "goal": {
                "action": parsed.target,
                "quantity": parsed.quantity,
                "unit": parsed.unit,
                "duration_value": parsed.duration_value,
                "duration_unit": parsed.duration_unit,
            },
        }
        return structured