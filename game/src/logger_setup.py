import logging
import os

# Logging configuration for ArcaneAI


httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

transitions_logger = logging.getLogger("transitions.core")
transitions_logger.setLevel(logging.WARNING)


def setup_logger(name="ArcaneAI"):
    # Hole das Log-Level aus der Environment-Variable
    log_level = os.getenv("ARCANEAI_LOG_LEVEL", "INFO").upper()

    # Erstelle einen Logger mit einem spezifischen Namen
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Verhindere, dass sich der Logger-Eintrag dupliziert
    if not logger.handlers:
        # Setze einen Handler und ein Format nur für diesen Logger
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# Create a logger instance that can be imported by other modules
logger = setup_logger()