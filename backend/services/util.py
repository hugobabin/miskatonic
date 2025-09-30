"""Service for handling useful functions and decorators."""

import os
import re, unicodedata
from typing import Annotated, Any

from dotenv import load_dotenv
from pydantic import BeforeValidator


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
    def normalize_question(s):
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


ObjectIdValidator = Annotated[str, BeforeValidator(ensure_str)]
