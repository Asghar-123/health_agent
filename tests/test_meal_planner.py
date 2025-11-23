import pytest
from tools.meal_planner import MealPlannerTool
from unittest.mock import AsyncMock, MagicMock
from agents import OpenAIChatCompletionsModel, AsyncOpenAI


@pytest.mark.asyncio
async def test_meal_planner_tool():
    """
    Tests the MealPlannerTool with a sample goal and diet preference.
    """
    # Create a mock for the AsyncOpenAI client
    mock_openai_client = AsyncMock()

    # Create a mock for the OpenAIChatCompletionsModel
    mock_model = MagicMock()

    # Configure the mock's chat method to return a predictable response
    mock_response = AsyncMock()  # Use AsyncMock for the return value
    mock_response.output_text = """
day_1:
- Breakfast: Oatmeal
- Lunch: Salad
- Dinner: Pasta
day_2:
- Breakfast: Cereal
- Lunch: Sandwich
- Dinner: Rice and beans
"""
    mock_model.chat.return_value = mock_response

    tool = MealPlannerTool()
    goal = {
        "action": "lose",
        "quantity": 5,
        "unit": "kg",
        "duration_value": 2,
        "duration_unit": "months",
    }
    result = await tool.run(mock_model, "vegetarian", goal)

    assert result["ok"] is True
    assert "meal_plan" in result
    assert isinstance(result["meal_plan"], dict)
    assert len(result["meal_plan"]) == 2
    assert "day_1" in result["meal_plan"]
    assert "day_2" in result["meal_plan"]
    mock_model.chat.assert_called_once()
