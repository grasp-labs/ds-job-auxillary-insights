"""Failure classification module."""

from classifier.categories import FailureCategory
from classifier.classifier import ClassifiedFailure, FailureClassifier

__all__ = ["ClassifiedFailure", "FailureCategory", "FailureClassifier"]
