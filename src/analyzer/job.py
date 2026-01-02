"""Daily failure analysis job."""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from classifier import ClassifiedFailure, FailureCategory, FailureClassifier
from db import get_db_session, get_failed_jobs

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of analyzing a single job execution."""

    job_id: str
    pipeline_id: str
    pipeline_name: str | None
    tenant_id: str
    finished_at: datetime | None
    total_errors: int
    classifications: list[ClassifiedFailure]
    primary_category: FailureCategory | None = None
    by_category: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Calculate derived fields."""
        # Count by category
        counts: dict[str, int] = defaultdict(int)
        for c in self.classifications:
            counts[c.category.value] += 1
        self.by_category = dict(counts)

        # Determine primary category
        if counts:
            primary = max(counts.items(), key=lambda x: x[1])[0]
            self.primary_category = FailureCategory(primary)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/reporting."""
        return {
            "job_id": self.job_id,
            "pipeline_id": self.pipeline_id,
            "pipeline_name": self.pipeline_name,
            "tenant_id": self.tenant_id,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "total_errors": self.total_errors,
            "primary_category": self.primary_category.value if self.primary_category else None,
            "by_category": self.by_category,
            "classifications": [c.to_dict() for c in self.classifications],
        }


@dataclass
class AnalysisSummary:
    """Summary of all analyzed jobs."""

    analyzed_at: datetime
    period_start: datetime
    period_end: datetime
    total_jobs: int
    total_errors: int
    by_category: dict[str, int]
    by_tenant: dict[str, int]
    by_pipeline: dict[str, int]
    results: list[AnalysisResult]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/reporting."""
        return {
            "analyzed_at": self.analyzed_at.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_jobs": self.total_jobs,
            "total_errors": self.total_errors,
            "by_category": self.by_category,
            "by_tenant": self.by_tenant,
            "by_pipeline": self.by_pipeline,
            "results": [r.to_dict() for r in self.results],
        }


class FailureAnalyzerJob:
    """
    Daily job that analyzes failed job executions.

    Queries failed jobs from the database, classifies errors,
    and produces an analysis summary.
    """

    def __init__(
        self,
        use_llm: bool = True,
        lookback_hours: int = 24,
    ) -> None:
        self.classifier = FailureClassifier(use_llm_fallback=use_llm)
        self.lookback_hours = lookback_hours

    def run(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        tenant_id: UUID | None = None,
    ) -> AnalysisSummary:
        """
        Run the analysis job.

        Args:
            since: Start time (defaults to lookback_hours ago)
            until: End time (defaults to now)
            tenant_id: Optional tenant filter

        Returns:
            AnalysisSummary with all results
        """
        now = datetime.now(timezone.utc)
        if until is None:
            until = now
        if since is None:
            since = now - timedelta(hours=self.lookback_hours)

        logger.info(f"Analyzing failures from {since} to {until}")

        # Fetch failed jobs
        with get_db_session() as session:
            jobs = get_failed_jobs(
                session=session,
                since=since,
                until=until,
                tenant_id=tenant_id,
            )

        logger.info(f"Found {len(jobs)} failed jobs to analyze")

        # Analyze each job
        results: list[AnalysisResult] = []
        for job in jobs:
            result = self._analyze_job(job)
            if result:
                results.append(result)

        # Build summary
        summary = self._build_summary(
            results=results,
            analyzed_at=now,
            period_start=since,
            period_end=until,
        )

        logger.info(
            f"Analysis complete: {summary.total_jobs} jobs, "
            f"{summary.total_errors} errors, "
            f"categories: {summary.by_category}"
        )

        return summary

    def _analyze_job(self, job: dict[str, Any]) -> AnalysisResult | None:
        """Analyze a single job execution."""
        try:
            data = job.get("data", {})
            run_info = data.get("run_info", {})

            if not run_info.get("errors"):
                return None

            classifications = self.classifier.classify_job_errors(run_info)

            return AnalysisResult(
                job_id=job["id"],
                pipeline_id=job["pipeline_id"],
                pipeline_name=job.get("pipeline_name"),
                tenant_id=job["tenant_id"],
                finished_at=job.get("finished_at"),
                total_errors=len(classifications),
                classifications=classifications,
            )
        except Exception as e:
            logger.error(f"Failed to analyze job {job.get('id')}: {e}")
            return None

    def _build_summary(
        self,
        results: list[AnalysisResult],
        analyzed_at: datetime,
        period_start: datetime,
        period_end: datetime,
    ) -> AnalysisSummary:
        """Build summary from analysis results."""
        by_category: dict[str, int] = defaultdict(int)
        by_tenant: dict[str, int] = defaultdict(int)
        by_pipeline: dict[str, int] = defaultdict(int)
        total_errors = 0

        for result in results:
            total_errors += result.total_errors
            by_tenant[result.tenant_id] += 1

            pipeline_key = result.pipeline_name or result.pipeline_id
            by_pipeline[pipeline_key] += 1

            for cat, count in result.by_category.items():
                by_category[cat] += count

        return AnalysisSummary(
            analyzed_at=analyzed_at,
            period_start=period_start,
            period_end=period_end,
            total_jobs=len(results),
            total_errors=total_errors,
            by_category=dict(by_category),
            by_tenant=dict(by_tenant),
            by_pipeline=dict(by_pipeline),
            results=results,
        )


# Lambda handler
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda handler for the analysis job."""
    logger.info(f"Starting failure analysis job with event: {event}")

    use_llm = event.get("use_llm", True)
    lookback_hours = event.get("lookback_hours", 24)
    tenant_id = event.get("tenant_id")

    job = FailureAnalyzerJob(
        use_llm=use_llm,
        lookback_hours=lookback_hours,
    )

    summary = job.run(
        tenant_id=UUID(tenant_id) if tenant_id else None,
    )

    return {
        "statusCode": 200,
        "body": json.dumps(summary.to_dict(), default=str),
    }


if __name__ == "__main__":
    # CLI entry point for local testing
    import sys

    logging.basicConfig(level=logging.INFO)

    job = FailureAnalyzerJob(use_llm="--no-llm" not in sys.argv)
    summary = job.run()

    print(json.dumps(summary.to_dict(), indent=2, default=str))
