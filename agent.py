import os
from typing import Any, Dict, List
from context import UserSessionContext
from tools.goal_analyzer import GoalAnalyzerTool
from tools.meal_planner import MealPlannerTool
from tools.workout_recommender import WorkoutRecommenderTool
from tools.scheduler import CheckinSchedulerTool
from tools.tracker import ProgressTrackerTool
from tools.hydration_tracker import HydrationTrackerTool
from agent_s.nutrition_expert_agent import NutritionExpertAgent
from agent_s.injury_support_agent import InjurySupportAgent
from agent_s.escalation_agent import EscalationAgent
from hooks import RunHooks

# 👇 Gemini client + model wrapper
from agents import AsyncOpenAI, OpenAIChatCompletionsModel, ModelTracing
from agents.run import RunConfig, ModelSettings


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
            "hydration_tracker": HydrationTrackerTool(),
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

        # Enhanced dynamic instructions based on user input for tone
        dynamic_instructions_tone = self._get_dynamic_instructions_tone(user_input)

        # --- Handle Medical Advice Queries First ---
        medical_keywords = ["symptoms", "diagnose", "condition", "thyroid", "medical advice"]
        if any(word in user_input.lower() for word in medical_keywords):
            return await self._handle_medical_query(user_input, ctx, dynamic_instructions_tone)

        # --- Log water intake (specific intent) ---
        if any(word in user_input.lower() for word in ["log water", "drank", "water intake"]):
            import re
            amount_ml = 0
            match = re.search(r'(\d+)\s*(ml|milliliters|cup|cups|oz|ounces)', user_input.lower())
            if match:
                amount = int(match.group(1))
                unit = match.group(2)
                if unit in ["cup", "cups"]:
                    amount_ml = amount * 240 # Assuming 1 cup = 240ml
                elif unit in ["oz", "ounces"]:
                    amount_ml = amount * 30 # Assuming 1 oz = 30ml
                else: # ml or milliliters
                    amount_ml = amount

            if amount_ml > 0:
                ht = self.tools["hydration_tracker"]
                await self.hooks.on_tool_start(ht.name, {"amount_ml": amount_ml})
                result = await ht.run(amount_ml, ctx)
                if result["ok"]:
                    return {"ok": True, "response": f"Logged {amount_ml}ml of water. Total today: {ctx.water_intake}ml."}
                else:
                    return {"ok": False, "response": "Failed to log water intake."}
            else:
                return {"ok": False, "response": "Please specify the amount of water to log (e.g., 'log 500ml water')."}

        # --- Proactive Tool Calling / Structured Goal Parsing ---
        # If user talks about goals, weight, exercise, etc., try to use goal_analyzer
        if any(word in user_input.lower() for word in ["goal", "weight", "exercise", "gain", "lose", "plan"]):
            ga = self.tools["goal_analyzer"]
            await self.hooks.on_tool_start(ga.name, user_input)
            parsed = await ga.run(user_input)

            if parsed.get("ok"):
                ctx.goal = parsed["goal"]
                # Then proceed to generate plans
                return await self._generate_plans_and_response(ctx, dynamic_instructions_tone)
            else:
                # If goal_analyzer can't parse, try to respond generally or re-prompt
                response_obj = await self.model.get_response(
                    system_instructions=dynamic_instructions_tone + " User query couldn't be parsed by goal analyzer. Try to give a helpful and encouraging response related to health goals or offer to try again.",
                    input=user_input,
                    model_settings=ModelSettings(),
                    tools=[],
                    output_schema=None,
                    handoffs=[],
                    tracing=ModelTracing.DISABLED,
                    previous_response_id=ctx.previous_response_id,
                )
                ctx.previous_response_id = response_obj.response_id
                return {"ok": False, "response": response_obj.output[0].content[0].text}


        # 🔹 Casual chat / General inquiries (fallback if no specific intent or tool usage)
        response_obj = await self.model.get_response(
            system_instructions=dynamic_instructions_tone + " You are a general health and wellness assistant. Provide helpful, encouraging, and informative responses within your expertise.",
            input=user_input,
            model_settings=ModelSettings(),
            tools=[],
            output_schema=None,
            handoffs=[],
            tracing=ModelTracing.DISABLED,
            previous_response_id=ctx.previous_response_id,
        )
        ctx.previous_response_id = response_obj.response_id
        return {"ok": True, "response": response_obj.output[0].content[0].text}

    async def _handle_medical_query(self, user_input: str, ctx: UserSessionContext, dynamic_instructions: str) -> Dict[str, Any]:
        """
        Handles medical-related queries by providing general information and a disclaimer.
        """
        # A more specific instruction for medical queries
        medical_instruction = "You are a health information assistant, not a medical professional. Provide general, publicly available information about the health topic requested, but *always* conclude by strongly advising the user to consult a qualified healthcare professional for diagnosis, treatment, and personalized medical advice. Do not diagnose or recommend treatments."

        response_obj = await self.model.get_response(
            system_instructions=dynamic_instructions + " " + medical_instruction,
            input=user_input,
            model_settings=ModelSettings(),
            tools=[],
            output_schema=None,
            handoffs=[],
            tracing=ModelTracing.DISABLED,
            previous_response_id=ctx.previous_response_id,
        )
        ctx.previous_response_id = response_obj.response_id
        return {"ok": True, "response": response_obj.output[0].content[0].text}

    async def _generate_plans_and_response(self, ctx: UserSessionContext, dynamic_instructions: str) -> Dict[str, Any]:
        """
        Generates meal and workout plans based on the user's goal and returns a structured response.
        """
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

    def _get_dynamic_instructions_tone(self, user_input: str) -> str:
        base_instruction = "You are a specialized AI assistant with expertise in health, biology, and medical queries. Your primary goal is to provide accurate, safe, and helpful information. Ensure your responses are concise, clear, and easy to understand, with a supportive and professional tone. Your maximum response length is 100 words."
        if "friendly" in user_input.lower():
            return base_instruction + " Also, maintain a very friendly and encouraging tone."
        elif "serious" in user_input.lower():
            return base_instruction + " Adopt a very serious and direct tone."
        elif "funny" in user_input.lower():
            return base_instruction + " Try to be humorous in your responses."
        else:
            return base_instruction