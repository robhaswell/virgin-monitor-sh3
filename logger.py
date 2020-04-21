"""
Logger which logs JSON to stdout.
"""
import logging
import sys

from pythonjsonlogger import jsonlogger


def start_logger():
    """
    Start logging to stdout.
    """
    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(jsonlogger.JsonFormatter(
        "%(asctime) $(name) %(levelname) %(message)"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)
