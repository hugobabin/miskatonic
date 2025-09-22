"""Question model based on BaseModel."""

from datetime import datetime
from typing import TypedDict

from pydantic import BaseModel


class QuestionModel(BaseModel):
    """Question."""

    question: str
    subject: str
    use: str
    responses: list[dict[str, str]]
    remark: str
    metadata: dict[str, str]
    date_creation: datetime
    date_modification: datetime | None  # noqa: FA102


class QuestionDict(TypedDict):
    """QuestionDict."""

    question: str
    subject: str
    use: str
    responses: list[dict[str, str]]
    remark: str
    metadata: dict[str, str]
    date_creation: datetime
    date_modification: datetime | None  # noqa: FA102


class QuestionGetter(BaseModel):
    """QuestionGetter."""

    subjects: list[str]
    use: str
