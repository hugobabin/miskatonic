"""Service for handling logs."""

import logging
import traceback
from pathlib import Path


class ServiceLog:
    """Service for handling logs."""

    dir = "/var/log"

    @staticmethod
    def setup() -> None:
        """Set up logging."""
        filename = f"{ServiceLog.dir}/app.log"
        path = Path(ServiceLog.dir)
        path.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=filename,
            level=logging.INFO,
            format="%(asctime)s %(levelname)s: %(message)s",
        )

    @staticmethod
    def send_info(message: str) -> None:
        """Log an info."""
        logger = logging.getLogger(__name__)
        logger.info(message)

    @staticmethod
    def send_exception(message: str, exc: Exception) -> None:
        """Log an exception."""
        logger = logging.getLogger(__name__)
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logger.error(f"{message}\n{tb}")
