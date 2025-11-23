import pytest
from tools.goal_analyzer import GoalAnalyzerTool


@pytest.mark.asyncio
async def test_goal_analyzer_tool():
    """
    Tests the GoalAnalyzerTool with a valid goal.
    """
    tool = GoalAnalyzerTool()
    result = await tool.run("lose 5kg in 2 months")

    assert result["ok"] is True
    assert result["goal"]["action"] == "lose"
    assert result["goal"]["quantity"] == 5
    assert result["goal"]["unit"] == "kg"
    assert result["goal"]["duration_value"] == 2
    assert result["goal"]["duration_unit"] == "months"
