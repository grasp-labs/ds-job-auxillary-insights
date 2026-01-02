"""Feedback system for improving LLM classifier with user corrections."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from classifier.categories import FailureCategory

logger = logging.getLogger(__name__)


class FeedbackStore:
    """Store and manage user feedback for classification corrections."""

    def __init__(self, feedback_file: Path | None = None):
        """
        Initialize feedback store.
        
        Args:
            feedback_file: Path to JSON file storing feedback. Defaults to data/feedback.json
        """
        if feedback_file is None:
            feedback_file = Path(__file__).parent.parent.parent / "data" / "feedback.json"

        self.feedback_file = feedback_file
        self.feedback_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize file if it doesn't exist
        if not self.feedback_file.exists():
            self._save_feedback([])

    def add_correction(
        self,
        job_id: str,
        activity_name: str,
        error: dict[str, Any],
        original_category: str,
        corrected_category: str,
        user: str | None = None,
        notes: str | None = None,
    ) -> None:
        """
        Record a user correction.
        
        Args:
            job_id: Job execution ID
            activity_name: Activity that failed
            error: Original error dict
            original_category: Category assigned by classifier
            corrected_category: Correct category from user
            user: Username/email of person making correction
            notes: Optional notes about why this correction was made
        """
        feedback = self._load_feedback()

        correction = {
            "timestamp": datetime.now(UTC).isoformat(),
            "job_id": job_id,
            "activity_name": activity_name,
            "error": error,
            "original_category": original_category,
            "corrected_category": corrected_category,
            "user": user,
            "notes": notes,
        }

        feedback.append(correction)
        self._save_feedback(feedback)

        logger.info(
            f"Recorded correction: {original_category} -> {corrected_category} "
            f"for job {job_id}, activity {activity_name}"
        )

    def get_corrections(
        self,
        category: FailureCategory | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get recorded corrections.
        
        Args:
            category: Filter by corrected category
            limit: Maximum number of corrections to return
            
        Returns:
            List of correction records
        """
        feedback = self._load_feedback()

        if category:
            feedback = [
                f for f in feedback
                if f["corrected_category"] == category.value
            ]

        # Sort by timestamp (newest first)
        feedback.sort(key=lambda x: x["timestamp"], reverse=True)

        if limit:
            feedback = feedback[:limit]

        return feedback

    def get_few_shot_examples(self, max_examples: int = 10) -> list[dict[str, Any]]:
        """
        Get recent corrections formatted as few-shot examples for LLM prompt.

        Args:
            max_examples: Maximum number of examples to return

        Returns:
            List of examples with error, activity, category, and reasoning
        """
        feedback = self._load_feedback()

        # Get most recent corrections
        feedback.sort(key=lambda x: x["timestamp"], reverse=True)
        feedback = feedback[:max_examples]

        examples = []
        for correction in feedback:
            examples.append({
                "activity_name": correction["activity_name"],
                "error": correction["error"],
                "category": correction["corrected_category"],
                "reasoning": correction.get("notes", "User-corrected classification"),
            })

        return examples

    def get_training_examples(self) -> list[dict[str, Any]]:
        """
        Get all corrections formatted as training examples for LLM.

        Returns:
            List of training examples with error and correct category
        """
        feedback = self._load_feedback()

        examples = []
        for correction in feedback:
            examples.append({
                "error": correction["error"],
                "activity_name": correction["activity_name"],
                "category": correction["corrected_category"],
                "notes": correction.get("notes"),
            })

        return examples

    def export_for_finetuning(self, output_file: Path) -> None:
        """
        Export corrections in JSONL format for LLM fine-tuning.
        
        Args:
            output_file: Path to output JSONL file
        """
        examples = self.get_training_examples()

        with open(output_file, "w") as f:
            for example in examples:
                # Format as OpenAI fine-tuning format
                training_example = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a workflow failure classifier. Classify errors into: INPUT_DATA_QUALITY, WORKFLOW_ENGINE, or THIRD_PARTY_SYSTEM."
                        },
                        {
                            "role": "user",
                            "content": f"Activity: {example['activity_name']}\nError: {json.dumps(example['error'])}"
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps({
                                "category": example["category"],
                                "reasoning": example.get("notes", "User-corrected classification")
                            })
                        }
                    ]
                }
                f.write(json.dumps(training_example) + "\n")

        logger.info(f"Exported {len(examples)} training examples to {output_file}")

    def _load_feedback(self) -> list[dict[str, Any]]:
        """Load feedback from file."""
        try:
            with open(self.feedback_file) as f:
                data: list[dict[str, Any]] = json.load(f)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_feedback(self, feedback: list[dict[str, Any]]) -> None:
        """Save feedback to file."""
        with open(self.feedback_file, "w") as f:
            json.dump(feedback, f, indent=2, default=str)

    def count(self) -> int:
        """Get total number of corrections."""
        return len(self._load_feedback())

