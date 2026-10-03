from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class DeliverableItem(BaseModel):
    course_name: str
    task_name: str
    due_date: Optional[str] = Field(None, description="YYYY-MM-DD, or null if only 'Week N' is given")
    relative_week: Optional[int] = None
    grade_weight_percent: float = Field(ge=0, le=100)
    task_type: Literal["exam", "project", "quiz", "assignment"]

    @field_validator("due_date")
    @classmethod
    def _iso_date(cls, v):
        if v is None:
            return v
        datetime.strptime(v, "%Y-%m-%d")  # raises ValueError if not ISO
        return v


class SyllabusData(BaseModel):
    items: List[DeliverableItem]
