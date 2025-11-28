#tool
#meal_planner.py
from typing import Any, Dict
from agents import OpenAIChatCompletionsModel


class MealPlannerTool:
    """
    A tool for generating a 7-day meal plan based on user preferences and goals.
    """
    name = "MealPlannerTool"

    async def run(
        self,
        model: OpenAIChatCompletionsModel,
        diet_preferences: str,
        parsed_goal: Dict,
    ) -> Dict[str, Any]:
        """
        Generates a 7-day meal plan using the Gemini model.

        Args:
            model: The Gemini model to use for generating the meal plan.
            diet_preferences: The user's dietary preferences.
            parsed_goal: A dictionary containing the user's parsed goal.

        Returns:
            A dictionary containing the 7-day meal plan.
        """
        prompt = f"""
        Generate a 7-day meal plan for a user with the following preferences and goals:
        - Diet: {diet_preferences}
        - Goal: {parsed_goal['action']} {parsed_goal['quantity']} {parsed_goal['unit']} in {parsed_goal['duration_value']} {parsed_goal['duration_unit']}

        The meal plan should include breakfast, lunch, dinner, and a snack for each day.
        Please provide the output in a structured format, with each day as a key (e.g., "day_1", "day_2", etc.) and the meals as a list of strings.
        """

        response = await model.chat(
            messages=[
                {"role": "system", "content": "You are a professional nutritionist."},
                {"role": "user", "content": prompt},
            ]
        )

        # A simple way to parse the response, assuming the model returns the plan in the expected format.
        # In a real-world scenario, you might want to use a more robust parsing method.
        meal_plan = {}
        current_day = None
        for line in response.output_text.split("\n"):
            line = line.strip()
            if line.lower().startswith("day_"):
                current_day = line.replace(":", "").lower()
                meal_plan[current_day] = []
            elif line and current_day:
                meal_plan[current_day].append(line)

        return {"ok": True, "meal_plan": meal_plan}