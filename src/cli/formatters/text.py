"""Plain text output formatter."""

from typing import Any

from cli.formatters.base import Formatter


class TextFormatter(Formatter):
    """Format analysis results as plain text."""

    def format(self, summary: dict[str, Any]) -> str:
        """Format summary as plain text with nice formatting."""
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("FAILURE ANALYSIS SUMMARY")
        lines.append("=" * 80)
        lines.append(f"\nAnalysis Period: {summary['period_start']} to {summary['period_end']}")
        lines.append(f"Analyzed At: {summary['analyzed_at']}")
        lines.append(f"\nTotal Failed Jobs: {summary['total_jobs']}")
        lines.append(f"Total Errors: {summary['total_errors']}")

        # Category breakdown
        lines.append("\n" + "-" * 80)
        lines.append("ERRORS BY CATEGORY")
        lines.append("-" * 80)

        by_category = summary.get("by_category", {})
        if by_category:
            for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / summary['total_errors'] * 100) if summary['total_errors'] > 0 else 0
                lines.append(f"  {category:25s}: {count:4d} ({percentage:5.1f}%)")
        else:
            lines.append("  No errors found")

        # Tenant breakdown
        lines.append("\n" + "-" * 80)
        lines.append("FAILED JOBS BY TENANT")
        lines.append("-" * 80)

        by_tenant = summary.get("by_tenant", {})
        if by_tenant:
            for tenant_id, count in sorted(by_tenant.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {tenant_id}: {count} jobs")
        else:
            lines.append("  No tenants found")

        # Pipeline breakdown
        lines.append("\n" + "-" * 80)
        lines.append("FAILED JOBS BY PIPELINE")
        lines.append("-" * 80)

        by_pipeline = summary.get("by_pipeline", {})
        if by_pipeline:
            for pipeline, count in sorted(by_pipeline.items(), key=lambda x: x[1], reverse=True)[:10]:
                lines.append(f"  {pipeline}: {count} jobs")
            if len(by_pipeline) > 10:
                lines.append(f"  ... and {len(by_pipeline) - 10} more pipelines")
        else:
            lines.append("  No pipelines found")

        # Detailed error table
        lines.append("\n" + "-" * 80)
        lines.append("ALL ERRORS - DETAILED BREAKDOWN")
        lines.append("-" * 80)

        results = summary.get("results", [])
        if results:
            # Header
            lines.append(f"\n{'Job ID':<10} {'Pipeline':<25} {'Activity':<20} {'Category':<20} {'By':<6} {'Error':<40}")
            lines.append("-" * 140)

            for result in results:
                job_id = result['job_id'][:8]
                pipeline = result.get('pipeline_name', 'Unknown')[:24]

                # Show each error classification
                for classification in result.get('classifications', []):
                    activity = classification.get('activity_name', 'N/A')[:19]
                    category = classification.get('category', 'UNKNOWN')[:19]
                    classified_by = classification.get('classified_by', 'unk')[:5]
                    error_msg = classification.get('original_error', {}).get('message', 'No message')[:39]

                    lines.append(f"{job_id:<10} {pipeline:<25} {activity:<20} {category:<20} {classified_by:<6} {error_msg:<40}")

            total_errors = sum(len(r.get('classifications', [])) for r in results)
            lines.append(f"\nTotal: {total_errors} errors across {len(results)} jobs")
        else:
            lines.append("  No errors found")

        lines.append("\n" + "=" * 80 + "\n")

        return "\n".join(lines)

