class InjurySupportAgent:
 name = 'InjurySupportAgent'


async def on_handoff(self, context, reason: str):
 context.handoff_logs.append(f'Injury handoff: {reason}')
 return {"ok": True}


async def run(self, query: str, context):
 return {"ok": True, "response": f"Injury-safe modifications for: {query}"}