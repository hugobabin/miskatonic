"""Service for handling useful functions."""

import os
import re
import unicodedata
from typing import Annotated, Any

from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import ORJSONResponse
from pydantic import BeforeValidator

from services.log import ServiceLog


class ServiceUtil:
    """Static class for handling useful functions."""

    @staticmethod
    def load_env() -> None:
        """Load environment file."""
        load_dotenv(".env")

    @staticmethod
    def get_env(var: str, default: str = "") -> str:
        """Get environment {var} or {default} value."""
        return os.getenv(var, default)

    @staticmethod
    def normalize_question(s: str) -> str:
        """Normalize questions."""
        if s is None:
            return ""
        s = unicodedata.normalize("NFKC", str(s)).strip()
        # remove trailing punctuation like : ; ? . ! …
        return re.sub(r"[ \t\u00A0]*[:;?.!…]+$", "", s)


def ensure_str(value: Any) -> Any:  # noqa: ANN401
    """Validate string values."""
    if not isinstance(value, str):
        return str(value)
    return value


def handle_request_success(
    request: Request,
    data: Any = None,  # noqa: ANN401
    message: str | None = None,
    status_code: int = 200,
) -> ORJSONResponse:
    """Standardize successful responses with logging."""
    ServiceLog.send_info(f"{request.url.path} -> {status_code}")
    return ORJSONResponse(
        content=data if data is not None else {"message": message},
        status_code=status_code,
    )


ObjectIdValidator = Annotated[str, BeforeValidator(ensure_str)]
