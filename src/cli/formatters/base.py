"""Base formatter interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Formatter(ABC):
    """Abstract base class for output formatters."""

    @abstractmethod
    def format(self, summary: dict[str, Any]) -> str:
        """
        Format the analysis summary.

        Args:
            summary: Analysis summary dictionary

        Returns:
            Formatted string output
        """

    def write(self, summary: dict[str, Any], output_path: Path | None = None) -> None:
        """
        Write formatted output to file or stdout.

        Args:
            summary: Analysis summary dictionary
            output_path: Optional output file path (None = stdout)
        """
        content = self.format(summary)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content)
        else:
            print(content)

