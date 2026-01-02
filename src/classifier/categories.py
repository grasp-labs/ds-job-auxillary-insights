"""Failure category definitions."""

from enum import StrEnum


class FailureCategory(StrEnum):
    """Categories for workflow failures."""

    INPUT_DATA_QUALITY = "INPUT_DATA_QUALITY"
    """Data validation failures, missing fields, format issues, schema mismatches."""

    WORKFLOW_ENGINE = "WORKFLOW_ENGINE"
    """Internal pipeline/activity execution issues, DAG errors, plugin failures."""

    THIRD_PARTY_SYSTEM = "THIRD_PARTY_SYSTEM"
    """External API failures, timeouts, authentication issues, rate limits."""

    UNKNOWN = "UNKNOWN"
    """Could not classify the failure."""
