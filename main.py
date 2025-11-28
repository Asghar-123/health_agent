import streamlit as st
from agent import HealthPlannerAgent
from context import UserSessionContext
import asyncio
import os
import json
import uuid

SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

def save_session_context(session_id: str, ctx: UserSessionContext):
    """Saves the UserSessionContext to a JSON file."""
    file_path = os.path.join(SESSION_DIR, f"{session_id}.json")
    with open(file_path, "w") as f:
        json.dump(ctx.model_dump(), f, indent=4)

def load_session_context(session_id: str) -> UserSessionContext:
    """Loads the UserSessionContext from a JSON file, or creates a new one if not found."""
    file_path = os.path.join(SESSION_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
            return UserSessionContext(**data)
    return UserSessionContext(uid=session_id) # Create new if not found, use existing session_id

# Initialize the agent and session context
if "health_agent" not in st.session_state:
    st.session_state.health_agent = HealthPlannerAgent()

    # Generate or retrieve a unique session ID for the Streamlit session
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Load existing session context or create a new one
    st.session_state.session_ctx = load_session_context(st.session_state.session_id)
    st.session_state.messages = []

st.set_page_config(page_title="Health Planner AI", page_icon="🏋️")
st.title("Health Planner AI")
st.write("I'm here to help you achieve your health and wellness goals!")

# Display chat messages from history on app rerun
for message_type, message_content in st.session_state.messages:
    with st.chat_message(message_type):
        st.markdown(message_content)

# Accept user input
if prompt := st.chat_input("Ask me anything about your health goals..."):
    # Add user message to chat history
    st.session_state.messages.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get agent's response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Run the agent in an async context
            # A workaround to run async code in Streamlit's sync environment
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    st.session_state.health_agent.run(prompt, st.session_state.session_ctx)
                )
            except Exception as e:
                result = {"ok": False, "response": f"An error occurred: {e}"}
            finally:
                loop.close()

            # Display agent response
            response_content = ""
            if result.get("ok"):
                if isinstance(result.get("response"), str):
                    response_content = result["response"]
                else: # Structured response
                    response_content = f"""
### 🎯 Goal
{result.get("goal", "Not set")}

### 🥗 Meal Plan
{result.get("meal_plan", "No meal plan generated")}

### 🏋️ Workout Plan
{result.get("workout_plan", "No workout plan generated")}

### 📋 Handoff Logs
{result.get("handoff_logs", "None")}
"""
            else:
                response_content = result.get("response", "An unknown error occurred.")

            st.markdown(response_content)
            st.session_state.messages.append(("assistant", response_content))
            
            # Save the updated session context after each interaction
            save_session_context(st.session_state.session_id, st.session_state.session_ctx)