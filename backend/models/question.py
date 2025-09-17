"""Question model based on TypedDict."""

from typing import TypedDict


class Question(TypedDict):
    """Question."""

    question: str
    subject: str
    use: str
    correct: list[str]
    responses: list[dict[str, str]]
    remark: str
    metadata: dict[str, str]
    date_creation: dict[str, str]
    date_modification: dict[str, str]
