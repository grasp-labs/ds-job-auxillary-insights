"""Failure classification module."""

from classifier.categories import FailureCategory
from classifier.classifier import ClassifiedFailure, FailureClassifier

__all__ = ["FailureCategory", "FailureClassifier", "ClassifiedFailure"]
