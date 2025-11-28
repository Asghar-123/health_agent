import pytest
from agent import HealthPlannerAgent
from context import UserSessionContext
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Mock the tools for testing purposes
class MockGoalAnalyzerTool:
    def __init__(self):
        self.name = "goal_analyzer"

    async def run(self, user_input: str):
        if "weight" in user_input.lower() or "exercise" in user_input.lower():
            return {"ok": True, "goal": "weight management"}
        return {"ok": False, "reason": "Could not parse goal"}

class MockHydrationTrackerTool:
    def __init__(self):
        self.name = "hydration_tracker"

    async def run(self, amount_ml: int, ctx: UserSessionContext):
        ctx.water_intake = getattr(ctx, "water_intake", 0) + amount_ml
        return {"ok": True}

class MockMealPlannerTool:
    def __init__(self):
        self.name = "meal_planner"

    async def run(self, model, diet_preferences, goal):
        return {"meal_plan": f"A personalized meal plan for {goal} with {diet_preferences}."}

class MockWorkoutRecommenderTool:
    def __init__(self):
        self.name = "workout_recommender"

    async def run(self, model, difficulty, goal):
        return {"workout_plan": f"A {difficulty} workout plan for {goal}."}

# --- New Mocks for Guardrails and Specialized Agents ---
class MockGuardrailManager:
    def __init__(self):
        self.pre_process_query = AsyncMock(return_value=(True, None))
        self.post_process_response = MagicMock(side_effect=lambda x, *args, **kwargs: f"{x} [TEST DISCLAIMER]")
        self.medical_disclaimer_text = "Medical disclaimer from mock guardrail."
        self.emergency_redirect_text = "Emergency redirect from mock guardrail."


class MockNutritionExpertAgent:
    def __init__(self, model):
        self.name = "nutrition_expert_agent"
        self.model = model
        self.on_handoff = AsyncMock(return_value={"ok": True})

    async def run(self, query: str, context):
        return {"ok": True, "response": f"Mock Nutrition Expert advice for: {query}"}

class MockInjurySupportAgent:
    def __init__(self, model):
        self.name = "injury_support_agent"
        self.model = model
        self.on_handoff = AsyncMock(return_value={"ok": True})

    async def run(self, query: str, context):
        return {"ok": True, "response": f"Mock Injury Support advice for: {query}. Please see a doctor."}

class MockEscalationAgent:
    def __init__(self, model):
        self.name = "escalation_agent"
        self.model = model # Store the passed model
        self.on_handoff = AsyncMock(return_value={"ok": True})

    async def run(self, query: str, context):
        return {"ok": True, "response": f"Mock Escalation for: {query}. Seek human expertise."}


@pytest.fixture
def health_planner_agent():
    agent = HealthPlannerAgent()
    # Replace real tools with mocks
    agent.tools["goal_analyzer"] = MockGoalAnalyzerTool()
    # agent.tools["hydration_tracker"] = MockHydrationTrackerTool() # hydration_tracker was commented out in agent.py
    agent.tools["meal_planner"] = MockMealPlannerTool()
    agent.tools["workout_recommender"] = MockWorkoutRecommenderTool()

    # Inject Mock GuardrailManager
    agent.guardrail_manager = MockGuardrailManager()

    # Inject Mock Specialized Agents
    # Assuming agent.model is already a mock from mock_get_response fixture
    mock_model_instance = MagicMock() # Use a simple MagicMock for passing to agents' __init__
    agent.handoffs["nutrition"] = MockNutritionExpertAgent(mock_model_instance)
    agent.handoffs["injury"] = MockInjurySupportAgent(mock_model_instance)
    agent.handoffs["escalation"] = MockEscalationAgent(mock_model_instance)

    return agent

@pytest.fixture(autouse=True)
def mock_get_response(monkeypatch):
    """Mocks the model.get_response method to return a predictable response."""
    async def mock_response(*args, **kwargs):
        system_instructions = kwargs.get("system_instructions", "")
        input_text = kwargs.get("input", "")

        # Simple logic to simulate model's response based on instructions and input
        if "friendly" in system_instructions:
            response_content = f"Friendly AI says: {input_text}"
        elif "serious" in system_instructions:
            response_content = f"Serious AI states: {input_text}"
        elif "humorous" in system_instructions:
            response_content = f"Funny AI quips: {input_text}"
        elif "medical information assistant" in system_instructions and "diagnosis" not in system_instructions:
            response_content = f"Based on general knowledge, your query about '{input_text}' relates to health. Remember to consult a healthcare professional for diagnosis and treatment."
        elif "User query couldn't be parsed by goal analyzer." in system_instructions: # Added for unparsed goal
            response_content = "User query couldn't be parsed by goal analyzer. Try to give a helpful and encouraging response related to health goals or offer to try again."
        elif "health goals" in system_instructions:
            response_content = f"Regarding your health goals query: {input_text}. Let's work towards them!"
        elif "nutrition expert providing general advice" in system_instructions:
             response_content = f"As a nutrition expert, I advise on {input_text}."
        elif "health information assistant, not a medical professional or injury specialist" in system_instructions:
            response_content = f"Regarding '{input_text}', please consult a doctor for injuries."
        elif "AI assistant clarifying your limitations" in system_instructions:
            response_content = f"I cannot fully address '{input_text}'. Seek human expertise."
        else:
            response_content = f"AI response to: {input_text}"

        # Mock response object structure from openai-agents
        class MockContent:
            def __init__(self, text):
                self.text = text

        class MockOutput:
            def __init__(self, content):
                self.content = content

        class MockResponseObj:
            def __init__(self, output, response_id):
                self.output = output
                self.response_id = response_id

        return MockResponseObj(output=[MockOutput(content=[MockContent(response_content)])], response_id="mock_id_123")

    monkeypatch.setattr("agent.OpenAIChatCompletionsModel.get_response", mock_response)


@pytest.mark.asyncio
async def test_guardrail_pre_process_blocks_emergency(health_planner_agent):
    health_planner_agent.guardrail_manager.pre_process_query.return_value = (False, "Emergency detected!")
    user_input = "I'm having a heart attack, help!"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is False
    assert "Emergency detected!" in response["response"]
    health_planner_agent.guardrail_manager.pre_process_query.assert_called_once_with(user_input)


@pytest.mark.asyncio
async def test_guardrail_pre_process_blocks_medical_diagnosis(health_planner_agent):
    health_planner_agent.guardrail_manager.pre_process_query.return_value = (False, "Medical diagnosis requests are not handled.")
    user_input = "Do I have strep throat?"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is False
    assert "Medical diagnosis requests are not handled." in response["response"]
    health_planner_agent.guardrail_manager.pre_process_query.assert_called_once_with(user_input)

@pytest.mark.asyncio
async def test_guardrail_post_process_adds_disclaimer_to_general_response(health_planner_agent):
    user_input = "Tell me about healthy eating."
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    # Check if the post-processing disclaimer was added
    assert "AI response to: Tell me about healthy eating. [TEST DISCLAIMER]" in response["response"]
    health_planner_agent.guardrail_manager.post_process_response.assert_called_once()

@pytest.mark.asyncio
async def test_injury_agent_integration(health_planner_agent):
    user_input = "My knee hurts after a run, what can I do?"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "Mock Injury Support advice for: My knee hurts after a run, what can I do?. Please see a doctor. [TEST DISCLAIMER]" in response["response"]
    health_planner_agent.handoffs["injury"].run.assert_called_once_with(user_input, ctx)
    health_planner_agent.guardrail_manager.post_process_response.assert_called_once()


@pytest.mark.asyncio
async def test_nutrition_expert_agent_integration(health_planner_agent):
    user_input = "What are good sources of protein?"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "Mock Nutrition Expert advice for: What are good sources of protein? [TEST DISCLAIMER]" in response["response"]
    health_planner_agent.handoffs["nutrition"].run.assert_called_once_with(user_input, ctx)
    health_planner_agent.guardrail_manager.post_process_response.assert_called_once()


@pytest.mark.asyncio
async def test_medical_query_handling_with_guardrail_passed(health_planner_agent):
    # This scenario now represents a query that passes pre-processing (not emergency/diagnosis)
    # but still relates to medical info, so it gets processed by _handle_medical_query
    # and then post-processed with the general disclaimer.
    user_input = "Tell me about the importance of sleep for overall health."
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    # The mock for get_response will return "AI response to: ..." or similar
    # And then the guardrail post-processor adds its disclaimer.
    assert "AI response to: Tell me about the importance of sleep for overall health. [TEST DISCLAIMER]" in response["response"]
    health_planner_agent.guardrail_manager.post_process_response.assert_called_once()



@pytest.mark.asyncio
async def test_log_water_intake(health_planner_agent):
    # Temporarily create a mock for hydration_tracker as it was commented out in agent.py
    health_planner_agent.tools["hydration_tracker"] = MockHydrationTrackerTool()
    user_input = "log 500ml water"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "Logged 500ml of water. (Hydration tracker functionality is currently simulated.) [TEST DISCLAIMER]" in response["response"]
    # ctx.water_intake check should be removed as the actual hydration tracker is commented out
    health_planner_agent.guardrail_manager.post_process_response.assert_called_once()

    health_planner_agent.guardrail_manager.post_process_response.reset_mock() # Reset for next part of test

    user_input = "drank 2 cups, friendly"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "Logged 480ml of water. (Hydration tracker functionality is currently simulated.) [TEST DISCLAIMER]" in response["response"] # 2 cups * 240ml
    # ctx.water_intake check should be removed as the actual hydration tracker is commented out
    health_planner_agent.guardrail_manager.post_process_response.assert_called_once()


@pytest.mark.asyncio
async def test_proactive_goal_analyzer_and_plan_generation(health_planner_agent):
    user_input = "I want to lose weight with exercise"
    ctx = UserSessionContext()
    ctx.diet_preferences = "vegetarian" # Simulate existing context
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert ctx.goal == "weight management"
    assert "A personalized meal plan for weight management with vegetarian." in response["meal_plan"]
    assert "A beginner workout plan for weight management." in response["workout_plan"]
    # Ensure disclaimer is applied to the final combined response text
    assert "Plans generated based on your goals. [TEST DISCLAIMER]" in response["response"]
    health_planner_agent.guardrail_manager.post_process_response.assert_called_once()


@pytest.mark.asyncio
async def test_proactive_goal_analyzer_unparsed(health_planner_agent):
    # Mock GoalAnalyzerTool to return not ok for this specific input
    class MockGoalAnalyzerToolFail:
        def __init__(self):
            self.name = "goal_analyzer"
        async def run(self, user_input: str):
            return {"ok": False, "reason": "Cannot parse"}
    health_planner_agent.tools["goal_analyzer"] = MockGoalAnalyzerToolFail()

    user_input = "My cat is fluffy"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is False
    assert "User query couldn't be parsed by goal analyzer. Try to give a helpful and encouraging response related to health goals or offer to try again. [TEST DISCLAIMER]" in response["response"]
    health_planner_agent.guardrail_manager.post_process_response.assert_called_once()


@pytest.mark.asyncio
async def test_general_inquiry_with_dynamic_tone(health_planner_agent):
    user_input = "Tell me about healthy eating, friendly"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "Friendly AI says: Tell me about healthy eating, friendly [TEST DISCLAIMER]" in response["response"]
    health_planner_agent.guardrail_manager.post_process_response.assert_called_once()

    health_planner_agent.guardrail_manager.post_process_response.reset_mock() # Reset for next part of test

    user_input = "What are good exercises for beginners, serious"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "Serious AI states: What are good exercises for beginners, serious [TEST DISCLAIMER]" in response["response"]
    health_planner_agent.guardrail_manager.post_process_response.assert_called_once()

@pytest.mark.asyncio
async def test_casual_chat_behavior(health_planner_agent):
    user_input = "Hello"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "AI response to: Hello [TEST DISCLAIMER]" in response["response"]
    health_planner_agent.guardrail_manager.post_process_response.assert_called_once()

    health_planner_agent.guardrail_manager.post_process_response.reset_mock() # Reset for next part of test

    user_input = "Hi there, friendly"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "Friendly AI says: Hi there, friendly [TEST DISCLAIMER]" in response["response"]