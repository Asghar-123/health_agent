#tool
#goal_analyzer.py
from typing import Any, Dict
import json
from agents import OpenAIChatCompletionsModel, ModelSettings
import enum

class ModelTracing(enum.Enum):
    DISABLED = 0
    """Tracing is disabled entirely."""

    ENABLED = 1
    """Tracing is enabled, and all data is included."""

    ENABLED_WITHOUT_DATA = 2
    """Tracing is enabled, but inputs/outputs are not included."""

    def is_disabled(self) -> bool:
        return self == ModelTracing.DISABLED

    def include_data(self) -> bool:
        return self == ModelTracing.ENABLED


class GoalAnalyzerTool:
    """
    A tool for analyzing and parsing health goals from raw text using an AI model.
    """
    name = "GoalAnalyzerTool"

    async def run(self, model: OpenAIChatCompletionsModel, raw_text: str) -> Dict[str, Any]:
        """
        Parses a health goal from raw text using the provided AI model.

        Args:
            model: The AI model to use for parsing.
            raw_text: The raw text containing the health goal.

        Returns:
            A dictionary containing the parsed goal information or an error message.
        """
        system_prompt = """
You are a highly intelligent goal analyzer. Your task is to parse the user's raw text and extract their health and fitness goal into a structured JSON object.

The JSON object should have the following fields:
- "name": A short, descriptive name for the goal (e.g., "Weight Loss", "Muscle Gain", "Improve Fitness").
- "action": The primary action (e.g., "lose", "gain", "increase", "improve").
- "quantity": The target amount, if specified (e.g., 10, 5).
- "unit": The unit for the quantity (e.g., "pounds", "kg", "percent", "biceps_size").
- "duration_value": The duration value, if specified (e.g., 3).
- "duration_unit": The unit for the duration (e.g., "months", "weeks").

Analyze the text and respond ONLY with the JSON object. Do not include any other text or formatting.

Example 1:
User raw text: "i want to lose 10 pounds in 3 months"
Your JSON response:
{
    "name": "Weight Loss",
    "action": "lose",
    "quantity": 10,
    "unit": "pounds",
    "duration_value": 3,
    "duration_unit": "months"
}

Example 2:
User raw text: "my goal is to get fit"
Your JSON response:
{
    "name": "Improve Fitness",
    "action": "improve",
    "quantity": null,
    "unit": "fitness_level",
    "duration_value": null,
    "duration_unit": null
}

Example 3:
User raw text: "i have goal of fitness and i want to increase biceps"
Your JSON response:
{
    "name": "Increase Biceps Size",
    "action": "increase",
    "quantity": null,
    "unit": "biceps_size",
    "duration_value": null,
    "duration_unit": null
}

Example 4:
User raw text: "i just want a meal plan"
Your JSON response:
{
    "name": "General Health",
    "action": "maintain",
    "quantity": null,
    "unit": null,
    "duration_value": null,
    "duration_unit": null
}
"""
        try:
            response_obj = await model.get_response(
                system_instructions=system_prompt,
                input=raw_text,
                model_settings=ModelSettings(temperature=0.0), # Use low temperature for predictable JSON
                tools=[],
                output_schema=None,
                handoffs=[],
                tracing=ModelTracing.DISABLED,
            )
            
            response_text = response_obj.output[0].content[0].text
            
            # Clean the response to ensure it's valid JSON
            # The model might sometimes include markdown ```json ... ```
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()

            parsed_goal = json.loads(response_text)
            
            return {
                "ok": True,
                "goal": parsed_goal
            }
        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            print(f"Error parsing goal from model response: {e}")
            return {"ok": False, "error": "Could not parse the goal. Please state your goal clearly."}
