"""Output formatters for analysis results."""

from typing import Type

from cli.formatters.base import Formatter
from cli.formatters.csv import CSVFormatter
from cli.formatters.json import JSONFormatter
from cli.formatters.text import TextFormatter

__all__ = [
    "CSVFormatter",
    "Formatter",
    "JSONFormatter",
    "TextFormatter",
]


def get_formatter(format_type: str) -> Formatter:
    """Factory function to get the appropriate formatter."""
    formatters: dict[str, type[Formatter]] = {
        "text": TextFormatter,
        "json": JSONFormatter,
        "csv": CSVFormatter,
    }

    formatter_class = formatters.get(format_type.lower())
    if not formatter_class:
        raise ValueError(f"Unknown format: {format_type}")

    return formatter_class()

