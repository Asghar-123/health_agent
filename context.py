# from typing import Optional, List, Dict
# from pydantic import BaseModel

# class UserSessionContext(BaseModel):
#     name: str
#     uid: int
#     goal: Optional[dict] = None
#     diet_preferences: Optional[str] = None
#     workout_plan: Optional[dict] = None
#     meal_plan: Optional[List[str]] = None
#     injury_notes: Optional[str] = None
#     handoff_logs: List[str] = []
#     progress_logs: List[Dict[str, str]] = []
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import uuid

class UserSessionContext(BaseModel):
    # Required but with defaults so instantiation won't break
    name: str = "Guest"
    uid: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Session data
    goal: Optional[Dict] = None
    diet_preferences: Optional[str] = None
    workout_plan: Optional[Dict] = None
    meal_plan: Optional[List[str]] = None
    injury_notes: Optional[str] = None

    # Logs with proper default factories (avoids shared mutable defaults)
    handoff_logs: List[str] = Field(default_factory=list)
    progress_logs: List[Dict[str, str]] = Field(default_factory=list)
