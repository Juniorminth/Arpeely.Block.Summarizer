import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure structured logging for the application.

    Uses a consistent format with timestamps and module names.
    Called once at startup from the lifespan context manager.
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger("arpeely")
    root.setLevel(level)
    root.addHandler(handler)
    root.propagate = False

