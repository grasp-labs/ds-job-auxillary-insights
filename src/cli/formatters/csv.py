"""CSV output formatter."""

import csv
import io
from pathlib import Path
from typing import Any

from cli.formatters.base import Formatter


class CSVFormatter(Formatter):
    """Format analysis results as CSV."""

    HEADERS = [
        "Job ID",
        "Pipeline Name",
        "Tenant ID",
        "Finished At",
        "Activity Name",
        "Error Category",
        "Classified By",
        "Confidence",
        "Reasoning",
        "Error Code",
        "Error Message",
        "Exception Type",
    ]

    def format(self, summary: dict[str, Any]) -> str:
        """Format summary as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(self.HEADERS)

        # Write data rows
        results = summary.get("results", [])
        for result in results:
            self._write_result_rows(writer, result)

        return output.getvalue()

    def _write_result_rows(self, writer: Any, result: dict[str, Any]) -> None:
        """Write CSV rows for a single job result."""
        job_id = result["job_id"]
        pipeline = result.get("pipeline_name", "Unknown")
        tenant_id = result.get("tenant_id", "Unknown")
        finished_at = result.get("finished_at", "Unknown")

        for classification in result.get("classifications", []):
            writer.writerow([
                job_id,
                pipeline,
                tenant_id,
                finished_at,
                classification.get("activity_name", "N/A"),
                classification.get("category", "UNKNOWN"),
                classification.get("classified_by", "unknown"),
                classification.get("confidence", 0.0),
                classification.get("reasoning", "N/A"),
                classification.get("original_error", {}).get("code", ""),
                classification.get("original_error", {}).get("message", "No message"),
                classification.get("original_error", {}).get("exception", "N/A"),
            ])

    def write(self, summary: dict[str, Any], output_path: Path | None = None) -> None:
        """Write CSV output with proper file handling."""
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(self.HEADERS)

                results = summary.get("results", [])
                for result in results:
                    self._write_result_rows(writer, result)
        else:
            print(self.format(summary))

