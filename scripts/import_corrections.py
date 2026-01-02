#!/usr/bin/env python3
"""Import user corrections from CSV to improve classifier."""

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

from classifier.feedback import FeedbackStore
from classifier.categories import FailureCategory

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def import_corrections_from_csv(csv_file: Path, user: str | None = None) -> int:
    """
    Import corrections from CSV file.
    
    Expected CSV format:
    - Must have columns: Job ID, Activity Name, Error Category, Error Message
    - Optional column: Corrected Category (if different from Error Category)
    - Optional column: Notes
    
    Args:
        csv_file: Path to CSV file with corrections
        user: Username/email of person making corrections
        
    Returns:
        Number of corrections imported
    """
    feedback_store = FeedbackStore()
    corrections_count = 0
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        
        # Validate required columns
        required_cols = ['Job ID', 'Activity Name', 'Error Category', 'Error Message']
        missing_cols = [col for col in required_cols if col not in reader.fieldnames]
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            logger.error(f"Available columns: {reader.fieldnames}")
            return 0
        
        for row in reader:
            job_id = row['Job ID']
            activity_name = row['Activity Name']
            original_category = row['Error Category']
            
            # Check if there's a correction
            corrected_category = row.get('Corrected Category', '').strip()
            if not corrected_category or corrected_category == original_category:
                # No correction needed
                continue
            
            # Validate corrected category
            try:
                FailureCategory(corrected_category)
            except ValueError:
                logger.warning(
                    f"Invalid category '{corrected_category}' for job {job_id}, skipping"
                )
                continue
            
            # Build error dict from CSV
            error = {
                'code': row.get('Error Code', ''),
                'message': row.get('Error Message', ''),
                'exception': row.get('Exception Type', ''),
                'details': {}
            }
            
            # Get notes if available
            notes = row.get('Notes', '') or row.get('Reasoning', '')
            
            # Add correction
            feedback_store.add_correction(
                job_id=job_id,
                activity_name=activity_name,
                error=error,
                original_category=original_category,
                corrected_category=corrected_category,
                user=user,
                notes=notes,
            )
            
            corrections_count += 1
            logger.info(
                f"Imported correction: {original_category} → {corrected_category} "
                f"(job {job_id[:8]}...)"
            )
    
    return corrections_count


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Import user corrections from CSV to improve classifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example workflow:
  1. Export errors to CSV:
     uv run python cli.py --format csv --output errors.csv
  
  2. Edit CSV and add 'Corrected Category' column for any misclassifications
  
  3. Import corrections:
     uv run python scripts/import_corrections.py errors.csv --user john@example.com
  
  4. Run analysis again - LLM will use corrections as examples!
     uv run python cli.py --hours 168

CSV Format:
  Required columns:
    - Job ID
    - Activity Name  
    - Error Category
    - Error Message
  
  Optional columns:
    - Corrected Category (add this to make corrections)
    - Notes (explain why the correction was made)
    - Error Code
    - Exception Type
        """,
    )
    
    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to CSV file with corrections",
    )
    parser.add_argument(
        "--user",
        type=str,
        help="Username/email of person making corrections",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.csv_file.exists():
        logger.error(f"File not found: {args.csv_file}")
        return 1
    
    logger.info(f"Importing corrections from {args.csv_file}...")
    count = import_corrections_from_csv(args.csv_file, args.user)
    
    if count > 0:
        logger.info(f"✅ Successfully imported {count} corrections!")
        logger.info("These will be used as examples in future LLM classifications.")
    else:
        logger.info("No corrections found in CSV (no 'Corrected Category' column or no changes)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

