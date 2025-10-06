"""Service for handling useful functions and decorators."""

import os
import re
import unicodedata

from typing import Annotated, Any
from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import ORJSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BeforeValidator
from pathlib import Path

from src.services.log import ServiceLog

BASE_DIR = Path(__file__).resolve().parents[2] 
ENV_PATH = BASE_DIR / ".env"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

class ServiceUtil:
    """Static class for handling useful functions."""

    @staticmethod
    def load_env() -> None:
        """Load environment file."""
        load_dotenv(ENV_PATH)

    @staticmethod
    def get_env(var: str, default: str = "") -> str:
        """Get environment {var} or {default} value."""
        return os.getenv(var, default)

    @staticmethod
    def normalize_question(s):
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
    message: str | None = None,  # noqa: FA102
    status_code: int = 200,
) -> ORJSONResponse:
    """Standardize successful responses with logging."""
    ServiceLog.send_info(f"{request.url.path} -> {status_code}")
    return ORJSONResponse(
        content=data if data is not None else {"message": message},
        status_code=status_code,
    )


def get_templates() -> Jinja2Templates:
    """Get Jinja2Templates."""
    return Jinja2Templates(directory=str(TEMPLATES_DIR.resolve()))



ObjectIdValidator = Annotated[str, BeforeValidator(ensure_str)]
