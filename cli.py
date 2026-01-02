#!/usr/bin/env python3
"""CLI for running failure analysis on job executions."""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from src.analyzer import FailureAnalyzerJob


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_markdown_summary(summary: dict) -> None:
    """Print analysis summary in Markdown format."""
    print("# Failure Analysis Report")
    print()
    print(f"**Analysis Period:** {summary['period_start']} to {summary['period_end']}  ")
    print(f"**Analyzed At:** {summary['analyzed_at']}  ")
    print()
    print("## Summary")
    print()
    print(f"- **Total Failed Jobs:** {summary['total_jobs']}")
    print(f"- **Total Errors:** {summary['total_errors']}")
    print()

    # Category breakdown
    print("## Errors by Category")
    print()
    by_category = summary.get("by_category", {})
    if by_category:
        print("| Category | Count | Percentage |")
        print("|----------|-------|------------|")
        for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / summary['total_errors'] * 100) if summary['total_errors'] > 0 else 0
            print(f"| {category} | {count} | {percentage:.1f}% |")
    else:
        print("*No errors found*")
    print()

    # Tenant breakdown
    print("## Failed Jobs by Tenant")
    print()
    by_tenant = summary.get("by_tenant", {})
    if by_tenant:
        print("| Tenant ID | Failed Jobs |")
        print("|-----------|-------------|")
        for tenant_id, count in sorted(by_tenant.items(), key=lambda x: x[1], reverse=True):
            print(f"| `{tenant_id}` | {count} |")
    else:
        print("*No tenant data*")
    print()

    # Pipeline breakdown
    print("## Failed Jobs by Pipeline")
    print()
    by_pipeline = summary.get("by_pipeline", {})
    if by_pipeline:
        print("| Pipeline | Failed Jobs |")
        print("|----------|-------------|")
        # Show top 20 pipelines
        for pipeline, count in sorted(by_pipeline.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"| {pipeline} | {count} |")

        remaining = len(by_pipeline) - 20
        if remaining > 0:
            print(f"| *...and {remaining} more pipelines* | |")
    else:
        print("*No pipeline data*")
    print()

    # Detailed error table
    print("## All Errors - Detailed Breakdown")
    print()
    print("| Job ID | Pipeline | Activity | Category | Classified By | Error Message | Finished At |")
    print("|--------|----------|----------|----------|---------------|---------------|-------------|")

    results = summary.get("results", [])
    if results:
        for result in results:
            job_id = result['job_id'][:8]  # Shortened for readability
            pipeline = result.get('pipeline_name', 'Unknown')[:30]  # Truncate long names
            finished_at = result.get('finished_at', 'Unknown')[:19] if result.get('finished_at') else 'Unknown'

            # Show each error classification
            for classification in result.get('classifications', []):
                activity = classification.get('activity_name', 'N/A')[:25]
                category = classification.get('category', 'UNKNOWN')
                classified_by = classification.get('classified_by', 'unknown')
                error_msg = classification.get('original_error', {}).get('message', 'No message')[:50]

                print(f"| {job_id} | {pipeline} | {activity} | {category} | {classified_by} | {error_msg} | {finished_at} |")
    else:
        print("| - | - | - | - | - | - | - |")
    print()

    # Detailed error breakdown by category
    print("## Detailed Error Analysis by Category")
    print()

    if results:
        # Group by category
        by_cat = {}
        for result in results:
            cat = result.get("primary_category", "UNKNOWN")
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(result)

        for category in sorted(by_cat.keys()):
            errors = by_cat[category]
            print(f"### {category} ({len(errors)} jobs)")
            print()

            # Show top 10 errors for this category
            for result in errors[:10]:
                print(f"#### Job: `{result['job_id']}`")
                print()
                print(f"- **Pipeline:** {result.get('pipeline_name', 'Unknown')}")
                print(f"- **Finished At:** {result.get('finished_at', 'Unknown')}")
                print(f"- **Total Errors:** {result.get('total_errors', 0)}")
                print()

                # Show classifications
                classifications = result.get("classifications", [])
                if classifications:
                    print("**Errors:**")
                    print()
                    for i, cls in enumerate(classifications[:3], 1):  # Show max 3 errors per job
                        print(f"{i}. **{cls.get('activity_name', 'Unknown')}**")
                        print(f"   - Category: `{cls.get('category', 'UNKNOWN')}`")
                        print(f"   - Confidence: {cls.get('confidence', 0):.2f}")
                        print(f"   - Reasoning: {cls.get('reasoning', 'N/A')}")

                        error = cls.get("original_error", {})
                        if error:
                            print(f"   - Exception: `{error.get('exception', 'Unknown')}`")
                            print(f"   - Message: {error.get('message', 'N/A')}")
                        print()

                    if len(classifications) > 3:
                        print(f"   *...and {len(classifications) - 3} more errors*")
                        print()
                print()

            if len(errors) > 10:
                print(f"*...and {len(errors) - 10} more jobs in this category*")
                print()
    else:
        print("*No detailed results available*")
    print()

    # Footer
    print("---")
    print()
    print("*Generated by ds-job-insights*")


def export_csv(summary: dict, output_file: Path | None = None) -> None:
    """Export detailed error data to CSV format."""
    import io

    output = io.StringIO() if output_file is None else open(output_file, 'w', newline='')

    try:
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Job ID',
            'Pipeline Name',
            'Tenant ID',
            'Finished At',
            'Activity Name',
            'Error Category',
            'Classified By',
            'Confidence',
            'Reasoning',
            'Error Code',
            'Error Message',
            'Exception Type'
        ])

        # Data rows
        results = summary.get("results", [])
        for result in results:
            job_id = result['job_id']
            pipeline = result.get('pipeline_name', 'Unknown')
            tenant_id = result.get('tenant_id', 'Unknown')
            finished_at = result.get('finished_at', 'Unknown')

            for classification in result.get('classifications', []):
                activity = classification.get('activity_name', 'N/A')
                category = classification.get('category', 'UNKNOWN')
                classified_by = classification.get('classified_by', 'unknown')
                confidence = classification.get('confidence', 0.0)
                reasoning = classification.get('reasoning', 'N/A')

                error = classification.get('original_error', {})
                error_code = error.get('code', '')
                error_msg = error.get('message', 'No message')
                exception = error.get('exception', 'N/A')

                writer.writerow([
                    job_id,
                    pipeline,
                    tenant_id,
                    finished_at,
                    activity,
                    category,
                    classified_by,
                    confidence,
                    reasoning,
                    error_code,
                    error_msg,
                    exception
                ])

        if output_file is None:
            print(output.getvalue())

    finally:
        if output_file is not None:
            output.close()


def print_summary(summary: dict, format: str = "text") -> None:
    """Print analysis summary in the specified format."""
    if format == "json":
        print(json.dumps(summary, indent=2, default=str))
        return

    if format == "markdown":
        print_markdown_summary(summary)
        return

    if format == "csv":
        export_csv(summary)
        return

    # Text format with nice formatting
    print("\n" + "=" * 80)
    print("FAILURE ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"\nAnalysis Period: {summary['period_start']} to {summary['period_end']}")
    print(f"Analyzed At: {summary['analyzed_at']}")
    print(f"\nTotal Failed Jobs: {summary['total_jobs']}")
    print(f"Total Errors: {summary['total_errors']}")

    # Category breakdown
    print("\n" + "-" * 80)
    print("ERRORS BY CATEGORY")
    print("-" * 80)
    by_category = summary.get("by_category", {})
    if by_category:
        for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / summary['total_errors'] * 100) if summary['total_errors'] > 0 else 0
            print(f"  {category:25s}: {count:4d} ({percentage:5.1f}%)")
    else:
        print("  No errors found")

    # Tenant breakdown
    print("\n" + "-" * 80)
    print("FAILED JOBS BY TENANT")
    print("-" * 80)
    by_tenant = summary.get("by_tenant", {})
    if by_tenant:
        for tenant_id, count in sorted(by_tenant.items(), key=lambda x: x[1], reverse=True):
            print(f"  {tenant_id}: {count} jobs")
    else:
        print("  No tenants found")

    # Pipeline breakdown
    print("\n" + "-" * 80)
    print("FAILED JOBS BY PIPELINE")
    print("-" * 80)
    by_pipeline = summary.get("by_pipeline", {})
    if by_pipeline:
        for pipeline, count in sorted(by_pipeline.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {pipeline}: {count} jobs")
        if len(by_pipeline) > 10:
            print(f"  ... and {len(by_pipeline) - 10} more pipelines")
    else:
        print("  No pipelines found")

    # Detailed error table
    print("\n" + "-" * 80)
    print("ALL ERRORS - DETAILED BREAKDOWN")
    print("-" * 80)
    results = summary.get("results", [])
    if results:
        # Header
        print(f"\n{'Job ID':<10} {'Pipeline':<25} {'Activity':<20} {'Category':<20} {'By':<6} {'Error':<40}")
        print("-" * 140)

        for result in results:
            job_id = result['job_id'][:8]
            pipeline = result.get('pipeline_name', 'Unknown')[:24]

            # Show each error classification
            for classification in result.get('classifications', []):
                activity = classification.get('activity_name', 'N/A')[:19]
                category = classification.get('category', 'UNKNOWN')[:19]
                classified_by = classification.get('classified_by', 'unk')[:5]
                error_msg = classification.get('original_error', {}).get('message', 'No message')[:39]

                print(f"{job_id:<10} {pipeline:<25} {activity:<20} {category:<20} {classified_by:<6} {error_msg:<40}")

        print(f"\nTotal: {sum(len(r.get('classifications', [])) for r in results)} errors across {len(results)} jobs")
    else:
        print("  No errors found")

    print("\n" + "=" * 80 + "\n")


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze failed job executions from ds-workflow-manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze last 24 hours with LLM (uses local Ollama by default)
  python cli.py

  # Analyze last 7 days, rules only (no LLM)
  python cli.py --hours 168 --no-llm

  # Use a different model
  python cli.py --llm-model qwen2.5:7b

  # Use a different LLM endpoint (e.g., LM Studio)
  python cli.py --llm-url http://localhost:1234/v1

  # Analyze specific time range
  python cli.py --since "2024-01-01 00:00:00" --until "2024-01-02 00:00:00"

  # Filter by tenant
  python cli.py --tenant-id "123e4567-e89b-12d3-a456-426614174000"

  # Generate markdown report
  python cli.py --format markdown --output report.md

  # Export to CSV for spreadsheet analysis
  python cli.py --format csv --output errors.csv

Environment Variables:
  BUILDING_MODE       Environment (dev/staging/prod) - default: dev
  DATABASE_URI        Override DB connection string (optional)
  LOCAL_LLM_MODEL     LLM model name - default: llama3.2:3b
  LOCAL_LLM_BASE_URL  LLM API URL - default: http://localhost:11434/v1
        """,
    )

    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Number of hours to look back (default: 24)",
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Start time (ISO format: YYYY-MM-DD HH:MM:SS)",
    )
    parser.add_argument(
        "--until",
        type=str,
        help="End time (ISO format: YYYY-MM-DD HH:MM:SS)",
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        help="Filter by tenant ID (UUID)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM fallback (use rules only)",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        help="LLM model name (e.g., llama3.2:3b, mistral, qwen2.5:7b) - default: llama3.2:3b",
    )
    parser.add_argument(
        "--llm-url",
        type=str,
        help="LLM API URL (default: http://localhost:11434/v1 for Ollama)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "csv"],
        default="text",
        help="Output format: text, json, markdown, or csv (default: text)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Parse arguments
        since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc) if args.since else None
        until = datetime.fromisoformat(args.until).replace(tzinfo=timezone.utc) if args.until else None
        tenant_id = UUID(args.tenant_id) if args.tenant_id else None

        # Set LLM environment variables if specified
        if args.llm_model:
            os.environ["LOCAL_LLM_MODEL"] = args.llm_model
        if args.llm_url:
            os.environ["LOCAL_LLM_BASE_URL"] = args.llm_url

        # Run analysis
        logger.info("Starting failure analysis...")

        job = FailureAnalyzerJob(
            use_llm=not args.no_llm,
            lookback_hours=args.hours,
        )

        summary = job.run(
            since=since,
            until=until,
            tenant_id=tenant_id,
        )

        # Convert to dict
        summary_dict = summary.to_dict()

        # Output results
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            if args.format == "json":
                with open(args.output, "w") as f:
                    json.dump(summary_dict, f, indent=2, default=str)
            elif args.format == "csv":
                export_csv(summary_dict, args.output)
            else:
                # Redirect stdout to file for text/markdown format
                with open(args.output, "w") as f:
                    old_stdout = sys.stdout
                    sys.stdout = f
                    print_summary(summary_dict, args.format)
                    sys.stdout = old_stdout
            logger.info(f"Results saved to {args.output}")
        else:
            print_summary(summary_dict, args.format)

        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
