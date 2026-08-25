from datetime import datetime

from pydantic import BaseModel, Field

from typing import Literal

Literal[
    "progression",
    "plateau",
    "recurring_issue",
    "insufficient_history",
]

class SetEntry(BaseModel):
    # Weight used for this individual set in kg
    weight: float

    # Reps completed in this individual set
    reps: int

class WorkoutEntry(BaseModel):
    # Name of the exercise
    exercise: str

    # Individual sets, preserving reps and weight for each set
    sets: list[SetEntry]

    # Rate of Perceived Exertion (1-10)
    rpe: int | None = Field(default=None, ge=1, le=10)

    # Optional notes from the workout journal
    notes: str | None = None

    # Timestamp assigned by our application
    timestamp: datetime | None = Field(
        default=None,
        description="Date and time when the workout was performed",
    )