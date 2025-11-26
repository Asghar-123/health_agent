import os
from typing import Any, Dict, List
from context import UserSessionContext
from tools.goal_analyzer import GoalAnalyzerTool
from tools.meal_planner import MealPlannerTool
from tools.workout_recommender import WorkoutRecommenderTool
from tools.scheduler import CheckinSchedulerTool
from tools.tracker import ProgressTrackerTool
#from tools.hydration_tracker import HydrationTrackerTool
from agent_s.nutrition_expert_agent import NutritionExpertAgent
from agent_s.injury_support_agent import InjurySupportAgent
from agent_s.escalation_agent import EscalationAgent
from hooks import RunHooks
from guardrails.guardrail_manager import GuardrailManager # Import GuardrailManager

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
        self._initialize_model() # Initialize model before handoffs
        self._initialize_handoffs()
        self.guardrail_manager = GuardrailManager() # Initialize GuardrailManager
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
            #"hydration_tracker": HydrationTrackerTool(),
        }

    def _initialize_handoffs(self):
        """
        Initializes the handoff agents.
        """
        self.handoffs = {
            "nutrition": NutritionExpertAgent(self.model),
            "injury": InjurySupportAgent(self.model),
            "escalation": EscalationAgent(self.model), # Pass the model to EscalationAgent
        }

    def _initialize_model(self):
        """
        Initializes the Gemini model.
        """
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        print(f"DEBUG: GEMINI_API_KEY (from os.getenv) = {gemini_api_key}")

        if not gemini_api_key:
            print("ERROR: GEMINI_API_KEY is not set in environment variables. AsyncOpenAI might fail.")
            raise ValueError("GEMINI_API_KEY is not set.")

        external_client = AsyncOpenAI(
            api_key=gemini_api_key, # Use the API key from environment or fallback
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

        self.model = OpenAIChatCompletionsModel(
            model="models/gemini-2.0-flash",  # Reverting to the user's preferred model
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

        # --- Guardrail Pre-processing ---
        passed_guardrail, refusal_message = self.guardrail_manager.pre_process_query(user_input)
        if not passed_guardrail:
            return {"ok": False, "response": refusal_message}

        # Enhanced dynamic instructions based on user input for tone
        dynamic_instructions_tone = self._get_dynamic_instructions_tone(user_input)

        # The old medical query check is replaced by the guardrail pre-processing.
        # Queries that are *general* health queries (not diagnosis/emergency) will proceed.

        # --- Handle Injury Queries ---
        injury_keywords = ["injury", "hurt", "pain", "sprain", "strain", "ache", "sore"]
        if any(word in user_input.lower() for word in injury_keywords):
            injury_agent = self.handoffs["injury"]
            await self.hooks.on_handoff("HealthPlannerAgent", "injury", user_input)
            injury_response = await injury_agent.run(user_input, ctx)
            response_text = injury_response.get("response", "Could not process injury query.")
            return {"ok": True, "response": self.guardrail_manager.post_process_response(response_text)}

        # --- Handle Nutrition Expert Queries ---
        nutrition_keywords = ["nutrition", "diet", "food", "healthy eating", "vitamins", "minerals", "protein", "carbs", "fats"]
        if any(word in user_input.lower() for word in nutrition_keywords) and not any(word in user_input.lower() for word in ["meal plan", "mealplanner"]): # Exclude meal plan requests as they go to a specific tool
            nutrition_agent = self.handoffs["nutrition"]
            await self.hooks.on_handoff("HealthPlannerAgent", "nutrition", user_input)
            nutrition_response = await nutrition_agent.run(user_input, ctx)
            response_text = nutrition_response.get("response", "Could not process nutrition query.")
            return {"ok": True, "response": self.guardrail_manager.post_process_response(response_text)}

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
                # Assuming "hydration_tracker" is enabled and correctly implemented
                # For now, commenting out as it was commented in original file.
                # ht = self.tools["hydration_tracker"]
                # await self.hooks.on_tool_start(ht.name, {"amount_ml": amount_ml})
                # result = await ht.run(amount_ml, ctx)
                # if result["ok"]:
                #    response_text = f"Logged {amount_ml}ml of water. Total today: {ctx.water_intake}ml."
                # else:
                #    response_text = "Failed to log water intake."
                response_text = f"Logged {amount_ml}ml of water. (Hydration tracker functionality is currently simulated.)"
                return {"ok": True, "response": self.guardrail_manager.post_process_response(response_text)}
            else:
                response_text = "Please specify the amount of water to log (e.g., 'log 500ml water')."
                return {"ok": False, "response": self.guardrail_manager.post_process_response(response_text)}

        # --- Proactive Tool Calling / Structured Goal Parsing ---
        # If user talks about goals, weight, exercise, etc., try to use goal_analyzer
        if any(word in user_input.lower() for word in ["goal", "weight", "exercise", "gain", "lose", "plan"]):
            ga = self.tools["goal_analyzer"]
            await self.hooks.on_tool_start(ga.name, user_input)
            parsed = await ga.run(user_input)

            if parsed.get("ok"):
                ctx.goal = parsed["goal"]
                # Then proceed to generate plans
                plans_response = await self._generate_plans_and_response(ctx, dynamic_instructions_tone)
                # Apply post-processing disclaimer to the final response
                if plans_response["ok"] and "response" in plans_response:
                    plans_response["response"] = self.guardrail_manager.post_process_response(plans_response["response"])
                return plans_response
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
                
                response_text = "Sorry, I couldn't process that query about your goals. Can you please rephrase?"
                if response_obj and response_obj.output and len(response_obj.output) > 0 and \
                   response_obj.output[0].content and len(response_obj.output[0].content) > 0 and \
                   hasattr(response_obj.output[0].content[0], 'text'):
                    response_text = response_obj.output[0].content[0].text
                else:
                    print(f"WARNING: Unexpected response structure from model in agent.py (goal_analyzer fallback): {response_obj}")
                return {"ok": False, "response": self.guardrail_manager.post_process_response(response_text)}


        # 🔹 Casual chat / General inquiries (fallback if no specific intent or tool usage)
        # For general health queries (not diagnosis/emergency related, as filtered by pre-processor)
        response_obj = await self.model.get_response(
        ctx.previous_response_id = response_obj.response_id
        
        response_text = "I'm sorry, I couldn't generate a response at this time. Please try again."
        if response_obj and response_obj.output and len(response_obj.output) > 0 and \
           response_obj.output[0].content and len(response_obj.output[0].content) > 0 and \
           hasattr(response_obj.output[0].content[0], 'text'):
            response_text = response_obj.output[0].content[0].text
        else:
            print(f"WARNING: Unexpected response structure from model in agent.py (general fallback): {response_obj}")
        return {"ok": True, "response": self.guardrail_manager.post_process_response(response_text)}


    async def _handle_medical_query(self, user_input: str, ctx: UserSessionContext, dynamic_instructions: str) -> Dict[str, Any]:
        """
        Handles medical-related queries. This method is now primarily for *general* health information
        that still requires a strong medical disclaimer, as true diagnosis/emergency queries
        are blocked by the pre-processor.
        """
        # The specific instruction for general medical queries now leverages the guardrail manager's disclaimer.
        medical_instruction = f"You are a health information assistant, not a medical professional. Provide general, publicly available information about the health topic requested. Append the following disclaimer: \"{self.guardrail_manager.medical_disclaimer_text}\". Do not diagnose or recommend treatments."

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
        
        response_text = "I'm sorry, I couldn't provide medical information at this time. Please try again."
        if response_obj and response_obj.output and len(response_obj.output) > 0 and \
           response_obj.output[0].content and len(response_obj.output[0].content) > 0 and \
           hasattr(response_obj.output[0].content[0], 'text'):
            response_text = response_obj.output[0].content[0].text
        else:
            print(f"WARNING: Unexpected response structure from model in agent.py (_handle_medical_query): {response_obj}")
        # The disclaimer is now part of the instruction to the model for better integration
        # No need for post_process_response here if the model already includes the medical_disclaimer_text
        # However, for consistency, let's still ensure a general disclaimer is added.
        return {"ok": True, "response": self.guardrail_manager.post_process_response(response_text)}


    async def _generate_plans_and_response(self, ctx: UserSessionContext, dynamic_instructions: str) -> Dict[str, Any]:
        """
        Generates meal and workout plans based on the user's goal and returns a structured response.
        """
        response_parts = []
        # 🔹 Meal plan
        if getattr(ctx, "diet_preferences", None):
            mp = self.tools["meal_planner"]
            await self.hooks.on_tool_start(mp.name, {"diet": ctx.diet_preferences, "goal": ctx.goal})
            meal = await mp.run(self.model, ctx.diet_preferences, ctx.goal)
            ctx.meal_plan = meal.get("meal_plan")
            if ctx.meal_plan:
                response_parts.append(f"Here is a meal plan: {ctx.meal_plan}")

        # 🔹 Workout plan
        wr = self.tools["workout_recommender"]
        await self.hooks.on_tool_start(wr.name, {"goal": ctx.goal})
        workout = await wr.run(self.model, "beginner", ctx.goal)
        ctx.workout_plan = workout.get("workout_plan")
        if ctx.workout_plan:
            response_parts.append(f"Here is a workout plan: {ctx.workout_plan}")

        # 🔹 Injury handoff
        if getattr(ctx, "injury_notes", None):
            await self.hooks.on_handoff("HealthPlannerAgent", "injury", ctx.injury_notes)
            await self.handoffs["injury"].on_handoff(ctx, ctx.injury_notes)
            response_parts.append("Your injury notes have been processed by the injury support system.")

        final_response_text = "\n".join(response_parts) if response_parts else "Plans generated based on your goals."

        # 🔹 Always return structured response
        return {
            "ok": True,
            "response": final_response_text, # Add the response text here
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