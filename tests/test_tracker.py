import pytest
from tools.tracker import ProgressTrackerTool
from context import UserSessionContext


@pytest.mark.asyncio
async def test_progress_tracker_tool():
    """
    Tests the ProgressTrackerTool with a sample context and update.
    """
    tool = ProgressTrackerTool()
    ctx = UserSessionContext()
    update = {"weight": 80, "unit": "kg"}
    result = await tool.run(ctx, update)

    assert result["ok"] is True
    assert "progress_logs" in result
    assert isinstance(result["progress_logs"], list)
    assert len(result["progress_logs"]) == 1
    assert result["progress_logs"][0] == update
