from typing import Any, Dict, List
from agents import OpenAIChatCompletionsModel


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
        Please provide the output as a list of strings, where each string represents a daily workout.
        """

        response = await model.chat(
            messages=[
                {"role": "system", "content": "You are a professional fitness coach."},
                {"role": "user", "content": prompt},
            ]
        )

        # A simple way to parse the response, assuming the model returns the plan as a list of strings.
        workout_plan = [line.strip() for line in response.output_text.split("\n") if line.strip()]

        return {"ok": True, "workout_plan": workout_plan}
