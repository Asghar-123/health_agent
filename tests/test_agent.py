import pytest
from agent import HealthPlannerAgent
from context import UserSessionContext
import asyncio


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

@pytest.fixture
def health_planner_agent():
    agent = HealthPlannerAgent()
    # Replace real tools with mocks
    agent.tools["goal_analyzer"] = MockGoalAnalyzerTool()
    agent.tools["hydration_tracker"] = MockHydrationTrackerTool()
    agent.tools["meal_planner"] = MockMealPlannerTool()
    agent.tools["workout_recommender"] = MockWorkoutRecommenderTool()
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
        elif "medical information assistant" in system_instructions:
            response_content = f"Based on general knowledge, your query about '{input_text}' relates to health. Remember to consult a healthcare professional for diagnosis and treatment."
        elif "health goals" in system_instructions:
            response_content = f"Regarding your health goals query: {input_text}. Let's work towards them!"
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
async def test_medical_query_handling(health_planner_agent):
    user_input = "What are the symptoms of thyroid?"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert "Based on general knowledge, your query about 'What are the symptoms of thyroid?' relates to health. Remember to consult a healthcare professional for diagnosis and treatment." in response["response"]

    user_input = "I need medical advice for my condition, be friendly."
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert "Friendly AI says: Based on general knowledge, your query about 'I need medical advice for my condition, be friendly.' relates to health." in response["response"]
    assert "Remember to consult a healthcare professional" in response["response"]

@pytest.mark.asyncio
async def test_log_water_intake(health_planner_agent):
    user_input = "log 500ml water"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "Logged 500ml of water." in response["response"]
    assert ctx.water_intake == 500

    user_input = "drank 2 cups, friendly"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "Logged 480ml of water." in response["response"] # 2 cups * 240ml
    assert ctx.water_intake == 980 # 500 + 480

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
    assert "User query couldn't be parsed by goal analyzer." in response["response"]

@pytest.mark.asyncio
async def test_general_inquiry_with_dynamic_tone(health_planner_agent):
    user_input = "Tell me about healthy eating, friendly"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "Friendly AI says: Tell me about healthy eating, friendly" in response["response"]

    user_input = "What are good exercises for beginners, serious"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "Serious AI states: What are good exercises for beginners, serious" in response["response"]

@pytest.mark.asyncio
async def test_casual_chat_behavior(health_planner_agent):
    user_input = "Hello"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "AI response to: Hello" in response["response"]

    user_input = "Hi there, friendly"
    ctx = UserSessionContext()
    response = await health_planner_agent.run(user_input, ctx)
    assert response["ok"] is True
    assert "Friendly AI says: Hi there, friendly" in response["response"]