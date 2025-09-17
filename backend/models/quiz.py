"""Quiz model based on TypedDict."""

from typing import TypedDict

from models.question import Question


class Quiz(TypedDict):
    """Quiz."""

    questions: list[Question]
    subjects: list[str]
    use: str
    metadata: dict[str, str]
    date_creation: dict[str, str]
    date_modification: dict[str, str]
