import os
from typing import Any, Dict, List
from context import UserSessionContext
from tools.goal_analyzer import GoalAnalyzerTool
from tools.meal_planner import MealPlannerTool
from tools.workout_recommender import WorkoutRecommenderTool
from tools.scheduler import CheckinSchedulerTool
from tools.tracker import ProgressTrackerTool
from agent_s.nutrition_expert_agent import NutritionExpertAgent
from agent_s.injury_support_agent import InjurySupportAgent
from agent_s.escalation_agent import EscalationAgent
from hooks import RunHooks

# 👇 Gemini client + model wrapper
from agents import AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig


class HealthPlannerAgent:
    """
    A health planner agent that generates meal and workout plans based on user goals.
    """

    def __init__(self):
        """
        Initializes the HealthPlannerAgent.
        """
        self._initialize_tools()
        self._initialize_handoffs()
        self._initialize_model()
        self.hooks = RunHooks()

    def _initialize_tools(self):
        """
        Initializes the tools for the agent.
        """
        self.tools = {
            "goal_analyzer": GoalAnalyzerTool(),
            "meal_planner": MealPlannerTool(),
            "workout_recommender": WorkoutRecommenderTool(),
            "scheduler": CheckinSchedulerTool(),
            "tracker": ProgressTrackerTool(),
        }

    def _initialize_handoffs(self):
        """
        Initializes the handoff agents.
        """
        self.handoffs = {
            "nutrition": NutritionExpertAgent(),
            "injury": InjurySupportAgent(),
            "escalation": EscalationAgent(),
        }

    def _initialize_model(self):
        """
        Initializes the Gemini model.
        """
        gemini_api_key = os.getenv("GEMINI_API_KEY")

        external_client = AsyncOpenAI(
            api_key=gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

        self.model = OpenAIChatCompletionsModel(
            model="gemini-2.0-flash",  # latest Gemini model
            openai_client=external_client,
        )

        self.config = RunConfig(
            model=self.model,
            model_provider=external_client,
            tracing_disabled=True,
        )

    async def run(self, user_input: str, ctx: UserSessionContext) -> Dict[str, Any]:
        """
        Runs the agent with the given user input and context.

        Args:
            user_input: The user's input message.
            ctx: The user's session context.

        Returns:
            A dictionary containing the agent's response.
        """
        await self.hooks.on_agent_start("HealthPlannerAgent", ctx)

        # 🔹 Casual chat → direct Gemini response
        if any(word in user_input.lower() for word in ["hello", "hi", "how are you", "thanks"]):
            response = await self.model.chat(
                messages=[
                    {"role": "system", "content": "You are a friendly Health & Wellness assistant."},
                    {"role": "user", "content": user_input},
                ]
            )
            return response.output_text

        # 🔹 Structured goal parsing
        ga = self.tools["goal_analyzer"]
        await self.hooks.on_tool_start(ga.name, user_input)
        parsed = await ga.run(user_input)

        if not parsed.get("ok"):
            # fallback: free text Gemini
            response = await self.model.chat(
                messages=[
                    {"role": "system", "content": "You are a professional health planner agent."},
                    {"role": "user", "content": user_input},
                ]
            )
            return response.output_text

        # Store structured goal
        ctx.goal = parsed["goal"]

        # 🔹 Meal plan
        if getattr(ctx, "diet_preferences", None):
            mp = self.tools["meal_planner"]
            await self.hooks.on_tool_start(mp.name, {"diet": ctx.diet_preferences, "goal": ctx.goal})
            meal = await mp.run(self.model, ctx.diet_preferences, ctx.goal)
            ctx.meal_plan = meal.get("meal_plan")

        # 🔹 Workout plan
        wr = self.tools["workout_recommender"]
        await self.hooks.on_tool_start(wr.name, {"goal": ctx.goal})
        workout = await wr.run(self.model, "beginner", ctx.goal)
        ctx.workout_plan = workout.get("workout_plan")

        # 🔹 Injury handoff
        if getattr(ctx, "injury_notes", None):
            await self.hooks.on_handoff("HealthPlannerAgent", "injury", ctx.injury_notes)
            await self.handoffs["injury"].on_handoff(ctx, ctx.injury_notes)

        # 🔹 Always return structured response
        return {
            "ok": True,
            "goal": ctx.goal,
            "meal_plan": getattr(ctx, "meal_plan", None),
            "workout_plan": getattr(ctx, "workout_plan", None),
            "handoff_logs": getattr(ctx, "handoff_logs", None),
        }