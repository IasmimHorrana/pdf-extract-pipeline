import sys

from loguru import logger

LOG_LEVEL = "INFO"


def setup_logging():
    """Configura loguru para o projeto."""
    logger.remove()

    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=LOG_LEVEL,
        colorize=True,
    )

    logger.add(
        "logs/pipeline_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
    )

    return logger


def get_logger(name: str = None):
    """Retorna logger configurado."""
    return logger.bind(name=name) if name else logger
