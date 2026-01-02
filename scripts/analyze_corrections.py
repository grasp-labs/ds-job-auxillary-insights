#!/usr/bin/env python3
"""Analyze user corrections to suggest new classification rules."""

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

from src.classifier.feedback import FeedbackStore
from src.classifier.categories import FailureCategory

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def analyze_patterns(min_occurrences: int = 3) -> dict:
    """
    Analyze corrections to find patterns that could become rules.
    
    Args:
        min_occurrences: Minimum number of similar corrections to suggest a rule
        
    Returns:
        Dict with pattern suggestions
    """
    feedback_store = FeedbackStore()
    corrections = feedback_store.get_corrections()
    
    if not corrections:
        logger.info("No corrections found yet.")
        return {}
    
    logger.info(f"Analyzing {len(corrections)} corrections...")
    
    # Group by category
    by_category = defaultdict(list)
    for correction in corrections:
        category = correction['corrected_category']
        by_category[category].append(correction)
    
    # Find patterns within each category
    suggestions = {}
    
    for category, items in by_category.items():
        logger.info(f"\n{category}: {len(items)} corrections")
        
        # Group by error message patterns
        message_patterns = defaultdict(list)
        activity_patterns = defaultdict(list)
        exception_patterns = defaultdict(list)
        
        for item in items:
            error = item['error']
            message = error.get('message', '').lower()
            exception = error.get('exception', '').lower()
            activity = item.get('activity_name', '').lower()
            
            # Extract key words from message
            words = re.findall(r'\w+', message)
            for word in words:
                if len(word) > 3:  # Skip short words
                    message_patterns[word].append(item)
            
            if exception:
                exception_patterns[exception].append(item)
            
            if activity:
                activity_patterns[activity].append(item)
        
        # Find patterns that occur frequently
        category_suggestions = []
        
        # Message patterns
        for pattern, matches in message_patterns.items():
            if len(matches) >= min_occurrences:
                category_suggestions.append({
                    'type': 'message',
                    'pattern': pattern,
                    'count': len(matches),
                    'suggested_rule': f'(r"{pattern}", "{category}", "Pattern from {len(matches)} user corrections")',
                    'examples': [m['error'].get('message', '')[:100] for m in matches[:3]]
                })
        
        # Exception patterns
        for pattern, matches in exception_patterns.items():
            if len(matches) >= min_occurrences:
                category_suggestions.append({
                    'type': 'exception',
                    'pattern': pattern,
                    'count': len(matches),
                    'suggested_rule': f'(r"{pattern}", "{category}", "Exception pattern from {len(matches)} corrections")',
                    'examples': [m['error'].get('exception', '') for m in matches[:3]]
                })
        
        # Activity patterns
        for pattern, matches in activity_patterns.items():
            if len(matches) >= min_occurrences:
                category_suggestions.append({
                    'type': 'activity',
                    'pattern': pattern,
                    'count': len(matches),
                    'suggested_rule': f'# Activity-specific: {pattern} → {category} ({len(matches)} corrections)',
                    'examples': [m.get('activity_name', '') for m in matches[:3]]
                })
        
        if category_suggestions:
            suggestions[category] = sorted(category_suggestions, key=lambda x: x['count'], reverse=True)
    
    return suggestions


def print_suggestions(suggestions: dict) -> None:
    """Print rule suggestions in a readable format."""
    if not suggestions:
        print("\n✅ No patterns found. Need more corrections to suggest rules.")
        print("   (Minimum 3 similar corrections required)")
        return
    
    print("\n" + "=" * 80)
    print("SUGGESTED RULES FROM USER CORRECTIONS")
    print("=" * 80)
    
    for category, patterns in suggestions.items():
        print(f"\n### {category}")
        print(f"Found {len(patterns)} potential rules:\n")
        
        for i, pattern in enumerate(patterns, 1):
            print(f"{i}. Pattern: '{pattern['pattern']}' ({pattern['type']})")
            print(f"   Occurrences: {pattern['count']}")
            print(f"   Suggested rule:")
            print(f"   {pattern['suggested_rule']}")
            print(f"   Examples:")
            for example in pattern['examples']:
                print(f"     - {example}")
            print()
    
    print("=" * 80)
    print("\n💡 To add these rules:")
    print("   1. Review the suggestions above")
    print("   2. Edit src/classifier/rules.py")
    print("   3. Add appropriate patterns to INPUT_DATA_PATTERNS, THIRD_PARTY_PATTERNS, or WORKFLOW_ENGINE_PATTERNS")
    print("   4. Test with: uv run python cli.py --hours 24 --no-llm")
    print()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze user corrections to suggest new classification rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--min-count",
        type=int,
        default=3,
        help="Minimum number of similar corrections to suggest a rule (default: 3)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save suggestions to JSON file",
    )
    
    args = parser.parse_args()
    
    suggestions = analyze_patterns(min_occurrences=args.min_count)
    
    print_suggestions(suggestions)
    
    if args.output and suggestions:
        with open(args.output, 'w') as f:
            json.dump(suggestions, f, indent=2)
        logger.info(f"Saved suggestions to {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

