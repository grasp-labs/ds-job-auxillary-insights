"""JSON output formatter."""

import json
from typing import Any

from cli.formatters.base import Formatter


class JSONFormatter(Formatter):
    """Format analysis results as JSON."""

    def format(self, summary: dict[str, Any]) -> str:
        """Format summary as pretty-printed JSON."""
        return json.dumps(summary, indent=2, default=str)

