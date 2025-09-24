"""Service for handling logs."""

import logging
from pathlib import Path


class ServiceLog:
    """Service for handling logs."""

    dir = "/var/log"  # inchangé

    @staticmethod
    def setup() -> None:
        """Set up logging."""
        # filename = f"{ServiceLog.dir}/app.log"                  # AVANT
        filename = Path(ServiceLog.dir) / "app.log"               # CHANGÉ

        path = Path(ServiceLog.dir)
        path.mkdir(parents=True, exist_ok=True)

        # logging.basicConfig(                                    # AVANT
        #     filename=filename,
        #     level=logging.INFO,
        #     format="%(asctime)s %(levelname)s: %(message)s",
        # )

        # Éviter les doublons en mode --reload                    # CHANGÉ
        if logging.getLogger().handlers:                          # CHANGÉ
            return                                                # CHANGÉ

        # Tentative fichier, repli stdout si PermissionError      # CHANGÉ
        try:                                                      # CHANGÉ
            logging.basicConfig(                                  # CHANGÉ
                filename=str(filename),                           # CHANGÉ
                level=logging.INFO,                               # CHANGÉ
                format="%(asctime)s %(levelname)s: %(message)s",  # CHANGÉ
            )                                                     # CHANGÉ
        except PermissionError:                                   # CHANGÉ
            logging.basicConfig(                                  # CHANGÉ
                level=logging.INFO,                               # CHANGÉ
                format="%(asctime)s %(levelname)s: %(message)s",  # CHANGÉ
            )                                                     # CHANGÉ

    @staticmethod
    def send(message: str) -> None:
        """Log a message."""
        logger = logging.getLogger(__name__)
        logger.propagate = False
        logger.info(message)
