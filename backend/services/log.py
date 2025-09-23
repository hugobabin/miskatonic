"""Service for handling logs."""

import logging
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
    def send(message: str) -> None:
        """Log a message."""
        logger = logging.getLogger(__name__)
        logger.propagate = False
        logger.info(message)
