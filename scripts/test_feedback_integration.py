#!/usr/bin/env python3
"""Quick test to verify feedback integration with classifier."""

import sys

from classifier.classifier import FailureClassifier
from classifier.feedback import FeedbackStore


def main():
    """Test feedback integration."""
    print("🧪 Testing Feedback Integration\n")
    print("=" * 60)

    # 1. Check feedback store
    print("\n1. Checking feedback store...")
    store = FeedbackStore()
    count = store.count()
    print("   ✅ Feedback store initialized")
    print(f"   📊 Total corrections: {count}")

    if count > 0:
        print("\n   Recent corrections:")
        examples = store.get_few_shot_examples(max_examples=3)
        for i, ex in enumerate(examples, 1):
            print(f"   {i}. {ex['activity_name']}: {ex['category']}")
            print(f"      {ex['reasoning'][:60]}...")

    # 2. Check classifier integration
    print("\n2. Checking classifier integration...")
    classifier = FailureClassifier(use_llm_fallback=True, use_few_shot_learning=True)
    print("   ✅ Classifier initialized")
    print(f"   📝 Few-shot learning: {classifier.use_few_shot_learning}")

    # 3. Test classification (without actually calling LLM)
    print("\n3. Testing classification flow...")
    test_error = {
        "code": 404,
        "message": "Test error for verification",
        "exception": "TestException",
        "details": {}
    }

    # This will use rules if available, otherwise would use LLM
    result = classifier.classify(test_error, activity_name="test_activity")
    print("   ✅ Classification works")
    print(f"   📊 Category: {result.category.value}")
    print(f"   🔧 Method: {result.classified_by}")

    # 4. Summary
    print("\n" + "=" * 60)
    print("✅ All checks passed!")
    print("\n📚 Next steps:")
    print("   1. Export errors: uv run python cli.py --format csv --output errors.csv")
    print("   2. Edit CSV and add 'Corrected Category' column")
    print("   3. Import: uv run python scripts/import_corrections.py errors.csv")
    print("   4. Run analysis: uv run python cli.py --hours 24")
    print("\n📖 Full guide: docs/feedback-loop.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())

