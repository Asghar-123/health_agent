# hooks.py

class RunHooks:
    async def on_agent_start(self, agent_name: str, ctx):
        print(f"[HOOK] Agent {agent_name} started for uid={ctx.uid}")

    async def on_tool_start(self, tool_name: str, input_data):
        print(f"[HOOK] Tool {tool_name} started with input={input_data}")

    async def on_handoff(self, from_agent: str, to_agent: str, context):
        print(f"[HOOK] Handoff from {from_agent} to {to_agent} with context={context}")
