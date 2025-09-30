import logging
import os


def configure_logging(default_level: str = "INFO") -> None:
    """
    Configure root logging once with a consistent format.

    Respects LOG_LEVEL env var (default INFO).
    """
    level_name = os.getenv("LOG_LEVEL", default_level).upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


