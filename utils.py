import os
from pathlib import Path


def debug(message, prefix="DEBUG"):
    """
    Print debug message in gray if DEBUG env var is true.

    Args:
        message: The debug message to print
        prefix: Prefix for the debug message (default: "DEBUG")
    """
    if os.getenv("DEBUG", "false").lower() == "true":
        print(f"    \033[38;5;108m[{prefix}] {message}\033[0m")


def record_user_input(value):
    """Append terminal input to the run log so the transcript is complete."""
    log_path = Path(os.getenv("TRAVEL_PLANNER_LOG", "logs/travel_planner.log"))
    if not log_path.is_absolute():
        log_path = Path(__file__).resolve().parent / log_path
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"Traveler input: {value}\n")
