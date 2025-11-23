# ExpertAgent:
# name = 'NutritionExpertAgent'


# async def on_handoff(self, context, reason: str):
# context.handoff_logs.append(f'Nutrition handoff: {reason}')
# return {"ok": True}


# async def run(self, query: str, context):
# return {"ok": True, "response": f"Nutrition expert advice for: {query}"}
class NutritionExpertAgent:
    name = 'NutritionExpertAgent'

    async def on_handoff(self, context, reason: str):
        if not hasattr(context, 'handoff_logs'):
            context.handoff_logs = []
        context.handoff_logs.append(f'Nutrition handoff: {reason}')
        return {"ok": True}

    async def run(self, query: str, context):
        return {"ok": True, "response": f"Nutrition expert advice for: {query}"}