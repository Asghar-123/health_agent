from typing import Any, Dict


class GoalAnalyzerTool:
    """
    A tool for analyzing and parsing health goals from raw text.
    """
    name = "GoalAnalyzerTool"

    async def run(self, raw_text: str) -> Dict[str, Any]:
        """
        Parses a health goal from raw text.
        For now, this is a simplified version that checks for keywords.

        Args:
            raw_text: The raw text containing the health goal.

        Returns:
            A dictionary containing the parsed goal information or an error message.
        """
        raw_text_lower = raw_text.lower()
        if "weight" in raw_text_lower or "gain" in raw_text_lower or "lose" in raw_text_lower:
            return {
                "ok": True,
                "goal": {
                    "action": "manage",
                    "quantity": "unknown",
                    "unit": "weight",
                    "duration_value": "unknown",
                    "duration_unit": "unknown",
                },
            }
        if "exercise" in raw_text_lower or "workout" in raw_text_lower:
            return {
                "ok": True,
                "goal": {
                    "action": "improve",
                    "quantity": "fitness",
                    "unit": "level",
                    "duration_value": "unknown",
                    "duration_unit": "unknown",
                },
            }
        return {"ok": False, "error": "Could not parse the goal. Please state your goal clearly."}