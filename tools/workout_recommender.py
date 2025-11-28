# # tool/workout_recommender.py
# from typing import Any, Dict
# from agents import OpenAIChatCompletionsModel
# from agents.run import ModelSettings
# from agents import ModelTracing

# class WorkoutRecommenderTool:
#     """
#     A tool for recommending a workout plan based on the user's goal and fitness level.
#     """
#     name = "WorkoutRecommenderTool"

#     async def run(
#         self,
#         model: OpenAIChatCompletionsModel,
#         level: str,
#         goal: Dict[str, Any],
#     ) -> Dict[str, Any]:
#         """
#         Recommends a workout plan based on the user's goal and fitness level.
#         """

#         prompt = f"""
# Generate a clear 7-day workout plan for:

# - Fitness Level: {level}
# - Goal: {goal.get("action", "")} {goal.get("quantity", "")} {goal.get("unit", "")}
#   in {goal.get("duration_value", "")} {goal.get("duration_unit", "")}

# IMPORTANT:
# - Return clean, human-readable normal text.
# - DO NOT return a Python list.
# - DO NOT wrap the plan inside brackets.
# - Format like:

# Day 1: ...
# Day 2: ...
# Day 3: ...
# """

#         response_obj = await model.get_response(
#             system_instructions="You are a professional fitness coach.",
#             input=prompt,
#             model_settings=ModelSettings(),
#             tools=[],
#             output_schema=None,
#             handoffs=[],
#             tracing=ModelTracing.DISABLED,
#         )

#         # Extract text safely
#         raw_text = response_obj.output[0].content[0].text or ""

#         # Remove any accidental brackets from Gemini
#         clean_text = raw_text.replace("[", "").replace("]", "").strip()

#         return {
#             "ok": True,
#             "workout_plan": clean_text   # <-- Return a STRING, not a list
#         }
# workout_recommender.py
from typing import Any, Dict
from agents import OpenAIChatCompletionsModel
from agents.run import ModelSettings
from agents import ModelTracing


class WorkoutRecommenderTool:
    """
    A tool for recommending a workout plan based on the user's goal and fitness level.
    """
    name = "WorkoutRecommenderTool"

    async def run(
        self,
        model: OpenAIChatCompletionsModel,
        level: str,
        goal: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Recommends a workout plan based on the user's goal and fitness level.

        Args:
            model: The Gemini model to use for generating the workout plan.
            level: The user's fitness level ('beginner', 'intermediate', or 'advanced').
            goal: A dictionary containing the user's parsed goal.

        Returns:
            A dictionary containing the recommended workout plan.
        """

        prompt = f"""
Generate a 7-day workout plan for a user with the following fitness level and goals:
- Fitness Level: {level}
- Goal: {goal.get("action", "")} {goal.get("quantity", "")} {goal.get("unit", "")} in {goal.get("duration_value", "")} {goal.get("duration_unit", "")}

The workout plan should be tailored to the user's fitness level and goals.
Provide the output as a list of lines (one workout per day).
"""

        # Call Gemini through OpenAI SDK
        response_obj = await model.get_response(
            system_instructions="You are a professional fitness coach.",
            input=prompt,
            model_settings=ModelSettings(),
            tools=[],
            output_schema=None,
            handoffs=[],
            tracing=ModelTracing.DISABLED,
        )

        # FIX: Safely combine all text tokens returned by model (no more characters issue)
        try:
            full_text = "".join(
                c.text
                for c in response_obj.output[0].content
                if hasattr(c, "text")
            )
        except Exception:
            full_text = ""

        # Convert combined text into a clean list
        workout_plan = [
            line.strip()
            for line in full_text.split("\n")
            if line.strip()
        ]

        return {
            "ok": True,
            "workout_plan": workout_plan
        }
