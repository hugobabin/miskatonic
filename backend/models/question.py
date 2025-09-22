"""Question model based on BaseModel."""

from datetime import datetime
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field
from services.util import ObjectIdValidator


class QuestionModel(BaseModel):
    """Question."""

    id: ObjectIdValidator = Field(alias="_id")
    question: str
    subject: str
    use: str
    responses: list[dict[str, str]]
    remark: str
    metadata: dict[str, str]
    date_creation: datetime
    date_modification: datetime | None  # noqa: FA102

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)


class QuestionDict(TypedDict):
    """QuestionDict."""

    id: str | None  # noqa: FA102
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
