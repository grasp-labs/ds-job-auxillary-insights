#!/usr/bin/env python3
"""Analyze LLM-classified errors to suggest new rule patterns.

This script helps you improve the rule-based classifier by:
1. Finding errors that were classified by LLM (not rules)
2. Identifying common patterns in those errors
3. Suggesting new regex patterns to add to rules.py

Usage:
    # Analyze last 30 days and suggest new patterns
    uv run python scripts/analyze_patterns.py --hours 720

    # Show top 20 patterns per category
    uv run python scripts/analyze_patterns.py --hours 720 --top 20

    # Only show patterns with at least 5 occurrences
    uv run python scripts/analyze_patterns.py --hours 720 --min-count 5
"""

import argparse
import logging
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer import FailureAnalyzerJob
from classifier import FailureCategory

logger = logging.getLogger(__name__)


def extract_keywords(text: str) -> list[str]:
    """Extract potential keywords from error text."""
    # Convert to lowercase
    text = text.lower()
    
    # Extract exception types (e.g., ValueError, KeyError)
    exceptions = re.findall(r'\b\w+(?:Error|Exception)\b', text)
    
    # Extract common error phrases
    phrases = []
    
    # Look for "X failed", "X error", "X not found", etc.
    patterns = [
        r'(\w+)\s+(?:failed|error|exception)',
        r'(?:failed|error)\s+(\w+)',
        r'(\w+)\s+not\s+found',
        r'invalid\s+(\w+)',
        r'missing\s+(\w+)',
        r'(\w+)\s+timeout',
        r'(\w+)\s+refused',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        phrases.extend(matches)
    
    # Extract HTTP status codes
    http_codes = re.findall(r'\b[4-5]\d{2}\b', text)
    
    return exceptions + phrases + http_codes


def suggest_patterns(results: list[dict], min_count: int = 3, top_n: int = 10) -> dict:
    """Analyze LLM-classified errors and suggest new patterns."""
    # Group by category
    by_category = defaultdict(list)
    
    for result in results:
        for classification in result.get("classifications", []):
            if classification.get("classified_by") == "llm":
                category = classification.get("category")
                error = classification.get("original_error", {})
                
                # Combine all error text
                text = " ".join([
                    str(error.get("message", "")),
                    str(error.get("exception", "")),
                    str(error.get("details", "")),
                ])
                
                by_category[category].append({
                    "text": text,
                    "activity": classification.get("activity_name"),
                    "reasoning": classification.get("reasoning"),
                })
    
    # Analyze patterns for each category
    suggestions = {}
    
    for category, errors in by_category.items():
        # Extract keywords from all errors
        keyword_counter = Counter()
        
        for error in errors:
            keywords = extract_keywords(error["text"])
            keyword_counter.update(keywords)
        
        # Get top keywords
        top_keywords = keyword_counter.most_common(top_n)
        
        # Filter by minimum count
        top_keywords = [(kw, count) for kw, count in top_keywords if count >= min_count]
        
        suggestions[category] = {
            "total_llm_classified": len(errors),
            "top_keywords": top_keywords,
            "sample_errors": errors[:3],  # Show 3 examples
        }
    
    return suggestions


def print_suggestions(suggestions: dict) -> None:
    """Print pattern suggestions in a readable format."""
    print("\n" + "=" * 80)
    print("PATTERN SUGGESTIONS FOR rules.py")
    print("=" * 80)
    print("\nThese patterns were found in errors classified by LLM.")
    print("Consider adding them to rules.py to make classification faster and free.\n")
    
    for category, data in suggestions.items():
        if not data["top_keywords"]:
            continue
            
        print(f"\n{'=' * 80}")
        print(f"{category}")
        print(f"{'=' * 80}")
        print(f"Total LLM-classified errors: {data['total_llm_classified']}")
        print(f"\nSuggested patterns to add to {category}_PATTERNS:")
        print()
        
        for keyword, count in data["top_keywords"]:
            # Suggest a regex pattern
            pattern = keyword.lower().replace("error", r".*error").replace("exception", r".*exception")
            print(f"    (r\"{pattern}\", \"{keyword} - found {count}x\"),")
        
        print(f"\nSample errors:")
        for i, error in enumerate(data["sample_errors"], 1):
            print(f"\n  {i}. Activity: {error['activity']}")
            print(f"     Reasoning: {error['reasoning']}")
            print(f"     Text: {error['text'][:200]}...")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze LLM-classified errors to suggest new rule patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--hours",
        type=int,
        default=168,  # 7 days
        help="Number of hours to analyze (default: 168 = 7 days)",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=3,
        help="Minimum occurrences to suggest a pattern (default: 3)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top patterns to show per category (default: 10)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    try:
        logger.info(f"Analyzing last {args.hours} hours...")
        
        # Run analysis with LLM enabled
        job = FailureAnalyzerJob(use_llm=True, lookback_hours=args.hours)
        summary = job.run()
        
        # Get suggestions
        suggestions = suggest_patterns(
            summary.to_dict()["results"],
            min_count=args.min_count,
            top_n=args.top,
        )
        
        # Print suggestions
        print_suggestions(suggestions)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())

