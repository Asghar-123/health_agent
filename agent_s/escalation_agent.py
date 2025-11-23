class EscalationAgent:
 name = 'EscalationAgent'


async def on_handoff(self, context, reason: str):
 context.handoff_logs.append(f'Escalation: {reason}')
 return {"ok": True}


async def run(self, query: str, context):
 return {"ok": True, "response": "A human coach will contact you (demo placeholder)."}