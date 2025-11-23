import pytest
from tools.scheduler import CheckinSchedulerTool


@pytest.mark.asyncio
async def test_checkin_scheduler_tool():
    """
    Tests the CheckinSchedulerTool with a sample level and cadence.
    """
    tool = CheckinSchedulerTool()
    result = await tool.run("beginner", cadence="weekly")

    assert result["ok"] is True
    assert result["scheduled"] is True
    assert result["cadence"] == "weekly"
    assert result["level"] == "beginner"
