"""Tests for feedback system."""

import json
import tempfile
from pathlib import Path

import pytest

from src.classifier.categories import FailureCategory
from src.classifier.feedback import FeedbackStore


@pytest.fixture
def temp_feedback_file():
    """Create a temporary feedback file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def test_add_correction(temp_feedback_file):
    """Test adding a correction."""
    store = FeedbackStore(feedback_file=temp_feedback_file)
    
    store.add_correction(
        job_id="test-123",
        activity_name="test_activity",
        error={"code": "404", "message": "Not found"},
        original_category="THIRD_PARTY_SYSTEM",
        corrected_category="INPUT_DATA_QUALITY",
        user="test@example.com",
        notes="Test correction",
    )
    
    assert store.count() == 1
    
    corrections = store.get_corrections()
    assert len(corrections) == 1
    assert corrections[0]["job_id"] == "test-123"
    assert corrections[0]["corrected_category"] == "INPUT_DATA_QUALITY"
    assert corrections[0]["user"] == "test@example.com"


def test_get_few_shot_examples(temp_feedback_file):
    """Test getting few-shot examples."""
    store = FeedbackStore(feedback_file=temp_feedback_file)
    
    # Add multiple corrections
    for i in range(5):
        store.add_correction(
            job_id=f"job-{i}",
            activity_name=f"activity_{i}",
            error={"message": f"Error {i}"},
            original_category="WORKFLOW_ENGINE",
            corrected_category="INPUT_DATA_QUALITY",
            notes=f"Reason {i}",
        )
    
    # Get few-shot examples
    examples = store.get_few_shot_examples(max_examples=3)
    
    assert len(examples) == 3
    assert all("activity_name" in ex for ex in examples)
    assert all("error" in ex for ex in examples)
    assert all("category" in ex for ex in examples)
    assert all("reasoning" in ex for ex in examples)
    
    # Should be most recent first
    assert examples[0]["activity_name"] == "activity_4"
    assert examples[1]["activity_name"] == "activity_3"
    assert examples[2]["activity_name"] == "activity_2"


def test_get_corrections_by_category(temp_feedback_file):
    """Test filtering corrections by category."""
    store = FeedbackStore(feedback_file=temp_feedback_file)
    
    # Add corrections for different categories
    store.add_correction(
        job_id="job-1",
        activity_name="activity_1",
        error={"message": "Error 1"},
        original_category="WORKFLOW_ENGINE",
        corrected_category="INPUT_DATA_QUALITY",
    )
    
    store.add_correction(
        job_id="job-2",
        activity_name="activity_2",
        error={"message": "Error 2"},
        original_category="INPUT_DATA_QUALITY",
        corrected_category="THIRD_PARTY_SYSTEM",
    )
    
    store.add_correction(
        job_id="job-3",
        activity_name="activity_3",
        error={"message": "Error 3"},
        original_category="WORKFLOW_ENGINE",
        corrected_category="INPUT_DATA_QUALITY",
    )
    
    # Filter by category
    input_data_corrections = store.get_corrections(
        category=FailureCategory.INPUT_DATA_QUALITY
    )
    assert len(input_data_corrections) == 2
    
    third_party_corrections = store.get_corrections(
        category=FailureCategory.THIRD_PARTY_SYSTEM
    )
    assert len(third_party_corrections) == 1


def test_get_corrections_with_limit(temp_feedback_file):
    """Test limiting number of corrections returned."""
    store = FeedbackStore(feedback_file=temp_feedback_file)
    
    # Add 10 corrections
    for i in range(10):
        store.add_correction(
            job_id=f"job-{i}",
            activity_name=f"activity_{i}",
            error={"message": f"Error {i}"},
            original_category="WORKFLOW_ENGINE",
            corrected_category="INPUT_DATA_QUALITY",
        )
    
    # Get only 5
    corrections = store.get_corrections(limit=5)
    assert len(corrections) == 5
    
    # Should be most recent first
    assert corrections[0]["job_id"] == "job-9"
    assert corrections[4]["job_id"] == "job-5"


def test_empty_feedback_store(temp_feedback_file):
    """Test behavior with no corrections."""
    store = FeedbackStore(feedback_file=temp_feedback_file)
    
    assert store.count() == 0
    assert store.get_corrections() == []
    assert store.get_few_shot_examples() == []


def test_persistence(temp_feedback_file):
    """Test that corrections persist across instances."""
    # Add correction with first instance
    store1 = FeedbackStore(feedback_file=temp_feedback_file)
    store1.add_correction(
        job_id="test-123",
        activity_name="test_activity",
        error={"message": "Test error"},
        original_category="WORKFLOW_ENGINE",
        corrected_category="INPUT_DATA_QUALITY",
    )
    
    # Load with second instance
    store2 = FeedbackStore(feedback_file=temp_feedback_file)
    assert store2.count() == 1
    
    corrections = store2.get_corrections()
    assert corrections[0]["job_id"] == "test-123"

