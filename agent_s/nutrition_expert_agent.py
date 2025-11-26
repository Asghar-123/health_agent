from typing import Any, Dict
from agents import OpenAIChatCompletionsModel # Import OpenAIChatCompletionsModel


class NutritionExpertAgent:
    name = 'NutritionExpertAgent'

    def __init__(self, model: OpenAIChatCompletionsModel): # Accept model in constructor
        self.model = model

    async def on_handoff(self, context, reason: str):
        if not hasattr(context, 'handoff_logs'):
            context.handoff_logs = []
        context.handoff_logs.append(f'Nutrition handoff: {reason}')
        return {"ok": True}

    async def run(self, query: str, context):
        # Use the model to generate nutrition expert advice
        prompt = f"Provide general nutrition advice or answer a specific nutrition question for the following query: '{query}'. Focus on healthy, balanced eating. Keep the response concise."

        response_obj = await self.model.get_response(
            system_instructions="You are a helpful nutrition expert providing general advice.",
            input=prompt,
            model_settings=None, # Use default model settings
            tools=[],
            output_schema=None,
            handoffs=[],
            tracing=None,
            previous_response_id=context.previous_response_id if hasattr(context, 'previous_response_id') else None,
        )
        context.previous_response_id = response_obj.response_id

        nutrition_advice = "Could not get nutrition advice."
        if response_obj and response_obj.output and len(response_obj.output) > 0 and \
           response_obj.output[0].content and len(response_obj.output[0].content) > 0 and \
           hasattr(response_obj.output[0].content[0], 'text'):
            nutrition_advice = response_obj.output[0].content[0].text
        else:
            print(f"WARNING: Unexpected response structure from model in NutritionExpertAgent: {response_obj}")

        return {"ok": True, "response": nutrition_advice}