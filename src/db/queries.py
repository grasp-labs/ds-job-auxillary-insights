"""Database queries for job execution data."""

import contextlib
import logging
import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import boto3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


def get_db_uri() -> str:
    """
    Get database URI from environment or SSM parameter.

    Priority:
    1. DATABASE_URI - Full connection string
    2. Individual DB_* environment variables (DB_HOST, DB_PORT, etc.)
    3. AWS SSM Parameter Store (/dsw/mgr/db_uri-{BUILDING_MODE})

    Returns:
        PostgreSQL connection URI
    """
    # Option 1: Full URI from environment
    if uri := os.environ.get("DATABASE_URI"):
        logger.debug("Using DATABASE_URI from environment")
        return uri

    # Option 2: Build URI from individual components
    if all(os.environ.get(k) for k in ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]):
        host = os.environ["DB_HOST"]
        port = os.environ.get("DB_PORT", "5432")
        name = os.environ["DB_NAME"]
        user = os.environ["DB_USER"]
        password = os.environ["DB_PASSWORD"]
        uri = f"postgresql://{user}:{password}@{host}:{port}/{name}"
        logger.debug(f"Built DATABASE_URI from components: {user}@{host}:{port}/{name}")
        return uri

    # Option 3: Fetch from SSM Parameter Store
    building_mode = os.environ.get("BUILDING_MODE", "dev")
    parameter_name = f"/dsw/mgr/db_uri-{building_mode}"

    logger.debug(f"Fetching database URI from SSM: {parameter_name}")
    ssm = boto3.client("ssm", region_name=os.environ.get("AWS_REGION", "eu-north-1"))
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    value: str = response["Parameter"]["Value"]
    return value


@contextlib.contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Create a database session context manager."""
    engine = create_engine(get_db_uri())
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_failed_jobs(
    session: Session,
    since: datetime | None = None,
    until: datetime | None = None,
    tenant_id: UUID | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """
    Query failed job executions from the database.

    Args:
        session: SQLAlchemy session
        since: Start time (defaults to 24 hours ago)
        until: End time (defaults to now)
        tenant_id: Optional tenant filter
        limit: Maximum number of results

    Returns:
        List of job execution dicts with id, pipeline_id, data, etc.
    """
    if since is None:
        since = datetime.now(UTC) - timedelta(hours=24)
    if until is None:
        until = datetime.now(UTC)

    query = text("""
        SELECT
            je.id,
            je.pipeline_id,
            je.session_id,
            je.tenant_id,
            je.status,
            je.data,
            je.started_at,
            je.finished_at,
            je.duration,
            p.name as pipeline_name
        FROM job_execution je
        LEFT JOIN pipeline p ON je.pipeline_id = p.id
        WHERE je.status = 'FAILURE'
          AND je.finished_at >= :since
          AND je.finished_at <= :until
          AND je.data IS NOT NULL
          AND je.data->>'run_info' IS NOT NULL
        ORDER BY je.finished_at DESC
        LIMIT :limit
    """)

    params: dict[str, Any] = {
        "since": since,
        "until": until,
        "limit": limit,
    }

    if tenant_id:
        query = text(query.text.replace(
            "ORDER BY",
            "AND je.tenant_id = :tenant_id ORDER BY"
        ))
        params["tenant_id"] = str(tenant_id)

    result = session.execute(query, params)
    rows = result.fetchall()

    return [
        {
            "id": str(row.id),
            "pipeline_id": str(row.pipeline_id),
            "pipeline_name": row.pipeline_name,
            "session_id": str(row.session_id),
            "tenant_id": str(row.tenant_id),
            "status": row.status,
            "data": row.data,
            "started_at": row.started_at,
            "finished_at": row.finished_at,
            "duration": str(row.duration) if row.duration else None,
        }
        for row in rows
    ]
