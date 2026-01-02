"""Tests for the failure classifier."""

import pytest

from classifier import FailureCategory, FailureClassifier


class TestFailureClassifier:
    """Tests for FailureClassifier."""

    @pytest.fixture
    def classifier(self) -> FailureClassifier:
        """Create classifier without LLM fallback for testing."""
        return FailureClassifier(use_llm_fallback=False)

    def test_classify_input_data_validation_error(
        self, classifier: FailureClassifier
    ) -> None:
        """Test classification of validation errors."""
        error = {
            "code": 400,
            "message": "Validation failed: missing required field 'customer_id'",
            "exception": "ValidationError",
            "details": {},
        }
        result = classifier.classify(error)

        assert result.category == FailureCategory.INPUT_DATA_QUALITY
        assert result.confidence == 0.9
        assert result.classified_by == "rules"

    def test_classify_input_data_empty_dataframe(
        self, classifier: FailureClassifier
    ) -> None:
        """Test classification of empty dataframe."""
        error = {
            "code": 500,
            "message": "DataFrame is empty, cannot proceed",
            "exception": "DataError",
            "details": {},
        }
        result = classifier.classify(error)

        assert result.category == FailureCategory.INPUT_DATA_QUALITY
        assert result.classified_by == "rules"

    def test_classify_third_party_xledger(
        self, classifier: FailureClassifier
    ) -> None:
        """Test classification of Xledger API error."""
        error = {
            "code": 500,
            "message": "Xledger API returned error: timeout after 30s",
            "exception": "XledgerError",
            "details": {"provider": "xledger"},
        }
        result = classifier.classify(error)

        assert result.category == FailureCategory.THIRD_PARTY_SYSTEM
        assert result.classified_by == "rules"

    def test_classify_third_party_timeout(
        self, classifier: FailureClassifier
    ) -> None:
        """Test classification of connection timeout."""
        error = {
            "code": 500,
            "message": "Connection timeout exceeded while fetching data",
            "exception": "TimeoutError",
            "details": {},
        }
        result = classifier.classify(error)

        assert result.category == FailureCategory.THIRD_PARTY_SYSTEM
        assert result.classified_by == "rules"

    def test_classify_third_party_auth_failure(
        self, classifier: FailureClassifier
    ) -> None:
        """Test classification of authentication failure."""
        error = {
            "code": 401,
            "message": "Authentication failed: invalid token",
            "exception": "AuthError",
            "details": {},
        }
        result = classifier.classify(error)

        assert result.category == FailureCategory.THIRD_PARTY_SYSTEM
        assert result.classified_by == "rules"

    def test_classify_workflow_engine_activity_not_found(
        self, classifier: FailureClassifier
    ) -> None:
        """Test classification of activity not found error."""
        error = {
            "code": 500,
            "message": "Activity not found: invalid_activity_id",
            "exception": "ActivityNotFoundError",
            "details": {},
        }
        result = classifier.classify(error)

        assert result.category == FailureCategory.WORKFLOW_ENGINE
        assert result.classified_by == "rules"

    def test_classify_workflow_engine_pipeline_exception(
        self, classifier: FailureClassifier
    ) -> None:
        """Test classification of pipeline exception."""
        error = {
            "code": 500,
            "message": "Pipeline execution failed",
            "exception": "PipelineException",
            "details": {},
        }
        result = classifier.classify(error)

        assert result.category == FailureCategory.WORKFLOW_ENGINE
        assert result.classified_by == "rules"

    def test_classify_unknown_error(
        self, classifier: FailureClassifier
    ) -> None:
        """Test classification of unknown error (no patterns match)."""
        error = {
            "code": 500,
            "message": "Something went wrong",
            "exception": "Exception",
            "details": {},
        }
        result = classifier.classify(error)

        assert result.category == FailureCategory.UNKNOWN
        assert result.classified_by == "none"

    def test_classify_http_4xx_as_input_error(
        self, classifier: FailureClassifier
    ) -> None:
        """Test that HTTP 4xx errors are classified as input errors."""
        error = {
            "code": 422,
            "message": "Unprocessable entity",
            "exception": "HTTPError",
            "details": {},
        }
        result = classifier.classify(error)

        assert result.category == FailureCategory.INPUT_DATA_QUALITY
        assert "HTTP 422" in result.reasoning

    def test_classify_job_errors(
        self, classifier: FailureClassifier
    ) -> None:
        """Test classifying all errors from a run_info dict."""
        run_info = {
            "errors": {
                "fetch_data": [
                    {
                        "code": 500,
                        "message": "Xledger timeout",
                        "exception": "TimeoutError",
                        "details": {},
                    }
                ],
                "validate_input": [
                    {
                        "code": 400,
                        "message": "Validation failed: missing field",
                        "exception": "ValidationError",
                        "details": {},
                    }
                ],
            }
        }

        results = classifier.classify_job_errors(run_info)

        assert len(results) == 2
        categories = {r.category for r in results}
        assert FailureCategory.THIRD_PARTY_SYSTEM in categories
        assert FailureCategory.INPUT_DATA_QUALITY in categories

    def test_classified_failure_to_dict(
        self, classifier: FailureClassifier
    ) -> None:
        """Test ClassifiedFailure serialization."""
        error = {"code": 500, "message": "Xledger error", "exception": "Error", "details": {}}
        result = classifier.classify(error, activity_name="test_activity")

        d = result.to_dict()

        assert d["category"] == "THIRD_PARTY_SYSTEM"
        assert d["activity_name"] == "test_activity"
        assert d["classified_by"] == "rules"
        assert "original_error" in d
