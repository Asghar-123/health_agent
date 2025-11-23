import pytest
from tools.workout_recommender import WorkoutRecommenderTool
from unittest.mock import AsyncMock, MagicMock
from agents import OpenAIChatCompletionsModel, AsyncOpenAI


@pytest.mark.asyncio
async def test_workout_recommender_tool():
    """
    Tests the WorkoutRecommenderTool with a sample goal.
    """
    # Create a mock for the AsyncOpenAI client
    mock_openai_client = AsyncMock()

    # Create a mock for the OpenAIChatCompletionsModel
    mock_model = MagicMock()

    # Configure the mock's chat method to return a predictable response
    mock_response = AsyncMock()  # Use AsyncMock for the return value
    mock_response.output_text = """
- Day 1: Cardio 30 mins
- Day 2: Strength training
- Day 3: Yoga
"""
    mock_model.chat.return_value = mock_response

    tool = WorkoutRecommenderTool()
    goal = {
        "action": "lose",
        "quantity": 5,
        "unit": "kg",
        "duration_value": 2,
        "duration_unit": "months",
    }
    result = await tool.run(mock_model, "beginner", goal)

    assert result["ok"] is True
    assert "workout_plan" in result
    assert isinstance(result["workout_plan"], list)
    assert len(result["workout_plan"]) > 0
    mock_model.chat.assert_called_once()
