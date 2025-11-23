from typing import Any, Dict, List
from context import UserSessionContext


class ProgressTrackerTool:
    """
    A tool for tracking user progress.
    """
    name = "ProgressTrackerTool"

    async def run(self, context: UserSessionContext, update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tracks user progress by appending an update to the progress logs.

        Args:
            context: The user's session context.
            update: A dictionary containing the progress update.

        Returns:
            A dictionary containing the updated progress logs.
        """
        if not hasattr(context, "progress_logs"):
            context.progress_logs = []

        context.progress_logs.append(update)
        return {"ok": True, "progress_logs": context.progress_logs}