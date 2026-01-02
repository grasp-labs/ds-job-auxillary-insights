"""Main failure classifier - combines rule-based and LLM classification."""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

import requests

from classifier.categories import FailureCategory
from classifier.feedback import FeedbackStore
from classifier.rules import (
    INPUT_DATA_PATTERNS,
    THIRD_PARTY_PATTERNS,
    WORKFLOW_ENGINE_PATTERNS,
)

logger = logging.getLogger(__name__)


@dataclass
class ClassifiedFailure:
    """Result of failure classification."""

    category: FailureCategory
    confidence: float
    reasoning: str
    original_error: dict[str, Any]
    activity_name: str | None = None
    classified_by: str = "rules"  # "rules", "llm", or "none"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "category": self.category.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "activity_name": self.activity_name,
            "classified_by": self.classified_by,
            "original_error": self.original_error,
        }


@dataclass
class FailureClassifier:
    """
    Classifies workflow failures into categories.

    Uses a two-stage approach:
    1. Rule-based pattern matching (fast, free, deterministic)
    2. LLM fallback for ambiguous cases (uses local LLM via OpenAI-compatible API)

    The LLM classifier uses any OpenAI-compatible endpoint (Ollama, LM Studio, etc.)
    Configure via environment variables:
    - LOCAL_LLM_MODEL: Model name (default: llama3.2:3b)
    - LOCAL_LLM_BASE_URL: API endpoint (default: http://localhost:11434/v1)
    """

    # LLM configuration
    DEFAULT_LLM_MODEL = "llama3.2:3b"
    DEFAULT_LLM_BASE_URL = "http://localhost:11434/v1"

    LLM_SYSTEM_PROMPT = """You are a workflow failure classifier for a data pipeline system.

Classify the error into exactly ONE of these categories:

1. INPUT_DATA_QUALITY - Problems with input data:
   - Validation failures, missing required fields
   - Wrong data format, schema mismatches
   - Empty or null values where data expected
   - Type conversion errors

2. WORKFLOW_ENGINE - Internal pipeline/orchestration issues:
   - Activity not found or misconfigured
   - Pipeline execution errors
   - DAG/dependency issues
   - Plugin or builtin failures
   - Context/state management errors

3. THIRD_PARTY_SYSTEM - External service failures:
   - API errors from external providers (Xledger, Visma, etc.)
   - HTTP errors, timeouts, connection issues
   - Authentication/authorization failures
   - Rate limiting, quota exceeded
   - SOAP/GraphQL/REST service errors

Respond with JSON only:
{
    "category": "INPUT_DATA_QUALITY|WORKFLOW_ENGINE|THIRD_PARTY_SYSTEM",
    "confidence": 0.0-1.0,
    "reasoning": "Brief one-sentence explanation"
}"""

    use_llm_fallback: bool = True
    use_few_shot_learning: bool = True  # Use corrections as examples in LLM prompt
    _llm_initialized: bool = field(default=False, init=False, repr=False)
    _llm_model: str = field(default="", init=False, repr=False)
    _llm_base_url: str = field(default="", init=False, repr=False)
    _llm_api_key: str = field(default="", init=False, repr=False)
    _feedback_store: FeedbackStore | None = field(default=None, init=False, repr=False)

    def _init_llm(self) -> None:
        """Initialize LLM configuration (lazy)."""
        if not self._llm_initialized:
            self._llm_model = os.getenv("LOCAL_LLM_MODEL", self.DEFAULT_LLM_MODEL)
            self._llm_base_url = os.getenv("LOCAL_LLM_BASE_URL", self.DEFAULT_LLM_BASE_URL)
            self._llm_api_key = os.getenv("LOCAL_LLM_API_KEY", "not-needed")
            self._feedback_store = FeedbackStore()
            self._llm_initialized = True
            logger.info(f"Initialized LLM classifier: {self._llm_model} at {self._llm_base_url}")

    def classify(
        self,
        error: dict[str, Any],
        activity_name: str | None = None,
    ) -> ClassifiedFailure:
        """
        Classify a single error into a failure category.

        Args:
            error: Error dict with keys: code, message, exception, details
            activity_name: Optional name of the activity that failed

        Returns:
            ClassifiedFailure with category, confidence, and reasoning
        """
        message = str(error.get("message", ""))
        exception = str(error.get("exception", ""))
        code = error.get("code", 0)
        details = error.get("details", {})

        # Combine text for pattern matching
        combined_text = f"{message} {exception} {json.dumps(details)}"

        # Stage 1: Rule-based classification
        result = self._classify_by_rules(combined_text, code)
        if result:
            category, reasoning = result
            return ClassifiedFailure(
                category=category,
                confidence=0.9,
                reasoning=reasoning,
                original_error=error,
                activity_name=activity_name,
                classified_by="rules",
            )

        # Stage 2: LLM fallback for ambiguous cases
        if self.use_llm_fallback:
            category, confidence, reasoning = self._classify_with_llm(error, activity_name)
            return ClassifiedFailure(
                category=category,
                confidence=confidence,
                reasoning=reasoning,
                original_error=error,
                activity_name=activity_name,
                classified_by="llm",
            )

        # No classification possible
        return ClassifiedFailure(
            category=FailureCategory.UNKNOWN,
            confidence=0.0,
            reasoning="No matching patterns and LLM disabled",
            original_error=error,
            activity_name=activity_name,
            classified_by="none",
        )

    def classify_job_errors(
        self,
        run_info: dict[str, Any],
    ) -> list[ClassifiedFailure]:
        """
        Classify all errors from a job execution run_info.

        Args:
            run_info: The run_info dict from JobExecution.data["run_info"]
                      Contains 'errors' dict mapping activity names to error lists

        Returns:
            List of ClassifiedFailure for each error
        """
        results = []
        errors_by_activity = run_info.get("errors", {})

        for activity_name, errors in errors_by_activity.items():
            for error in errors:
                classified = self.classify(error, activity_name)
                results.append(classified)

        return results

    def _classify_by_rules(
        self,
        text: str,
        code: int,
    ) -> tuple[FailureCategory, str] | None:
        """
        Attempt to classify using pattern matching rules.

        Returns (category, reasoning) or None if no match.
        """
        # Check input data patterns
        for pattern, reasoning in INPUT_DATA_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.debug(f"Matched INPUT_DATA pattern: {pattern}")
                return (FailureCategory.INPUT_DATA_QUALITY, reasoning)

        # Check third-party patterns
        for pattern, reasoning in THIRD_PARTY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.debug(f"Matched THIRD_PARTY pattern: {pattern}")
                return (FailureCategory.THIRD_PARTY_SYSTEM, reasoning)

        # Check workflow engine patterns
        for pattern, reasoning in WORKFLOW_ENGINE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.debug(f"Matched WORKFLOW_ENGINE pattern: {pattern}")
                return (FailureCategory.WORKFLOW_ENGINE, reasoning)

        # HTTP status code heuristics
        if 400 <= code < 500:
            return (FailureCategory.INPUT_DATA_QUALITY, f"HTTP {code} client error")

        return None

    def _classify_with_llm(
        self,
        error: dict[str, Any],
        activity_name: str | None = None,
    ) -> tuple[FailureCategory, float, str]:
        """
        Classify an error using local LLM with few-shot learning from corrections.

        Args:
            error: Error dict with code, message, exception, details
            activity_name: Optional activity name for context

        Returns:
            Tuple of (category, confidence, reasoning)
        """
        self._init_llm()

        # Build user prompt with few-shot examples from corrections
        user_prompt = ""

        # Add few-shot examples if enabled and available
        if self.use_few_shot_learning and self._feedback_store:
            examples = self._feedback_store.get_few_shot_examples(max_examples=5)
            if examples:
                user_prompt += "Here are some recent corrections from users:\n\n"
                for i, example in enumerate(examples, 1):
                    user_prompt += f"{i}. Activity: {example['activity_name']}\n"
                    user_prompt += f"   Error: {example['error'].get('message', 'N/A')}\n"
                    user_prompt += f"   Correct Category: {example['category']}\n"
                    user_prompt += f"   Reason: {example['reasoning']}\n\n"

                user_prompt += "Now classify this new error:\n\n"

        user_prompt += f"""Activity: {activity_name or 'Unknown'}
Error Code: {error.get('code')}
Message: {error.get('message')}
Exception Type: {error.get('exception')}
Details: {json.dumps(error.get('details', {}), indent=2)}"""

        try:
            # Call OpenAI-compatible API
            response = requests.post(
                f"{self._llm_base_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._llm_api_key}",
                },
                json={
                    "model": self._llm_model,
                    "messages": [
                        {"role": "system", "content": self.LLM_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,  # Low temperature for consistent classification
                    "max_tokens": 200,
                },
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Extract JSON from response (handle markdown code blocks)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # Parse JSON response
            classification = json.loads(content)

            return (
                FailureCategory(classification["category"]),
                float(classification["confidence"]),
                classification["reasoning"],
            )

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to local LLM at {self._llm_base_url}: {e}")
            return (
                FailureCategory.UNKNOWN,
                0.0,
                f"Local LLM connection failed: {e!s}",
            )
        except Exception as e:
            logger.error(f"Local LLM classification failed: {e}")
            return (
                FailureCategory.UNKNOWN,
                0.0,
                f"Local LLM classification failed: {e!s}",
            )
