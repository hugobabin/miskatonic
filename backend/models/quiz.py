"""Quiz model based on BaseModel."""

from models.question import QuestionModel
from pydantic import BaseModel


class Quiz(BaseModel):
    """Quiz."""

    questions: list[QuestionModel]
    subjects: list[str]
    use: str
    metadata: dict[str, str]
    date_creation: dict[str, str]
    date_modification: dict[str, str]


class QuizGenerator(BaseModel):
    """Quiz generator."""

    total_questions: int
    subjects: list[str]
    use: str
