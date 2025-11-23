import chainlit as cl
from agent import HealthPlannerAgent
from context import UserSessionContext

agent = HealthPlannerAgent()


@cl.on_message
async def main(message: cl.Message):
    """
    Main function that runs when a new message is received.

    Args:
        message: The message object from chainlit.
    """
    # Create a new session context for each user
    session_ctx = UserSessionContext()

    user_input = message.content

    result = await agent.run(user_input, session_ctx)

    # If the agent returned plain text → show directly
    if isinstance(result, str):
        await cl.Message(content=result).send()

    # If the agent returned structured dict → pretty print
    elif isinstance(result, dict):
        response_text = f"""
### 🎯 Goal
{result.get("goal", "Not set")}

### 🥗 Meal Plan
{result.get("meal_plan", "No meal plan generated")}

### 🏋️ Workout Plan
{result.get("workout_plan", "No workout plan generated")}

### 📋 Handoff Logs
{result.get("handoff_logs", "None")}
"""
        await cl.Message(content=response_text).send()

    else:
        await cl.Message(content="⚠️ Unexpected response from agent").send()
