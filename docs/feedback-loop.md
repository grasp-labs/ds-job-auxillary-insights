# Feedback Loop: Improving the Classifier

This guide explains how to correct misclassifications and use those corrections to improve the classifier over time.

## 🎯 Overview

The classifier uses a **hybrid approach** that combines:

1. **Rules** (fast, free, deterministic)
2. **LLM with Few-Shot Learning** (smart, learns from corrections)
3. **Pattern Analysis** (suggests new rules from corrections)

```
User Corrections → Few-Shot Learning (immediate) → Pattern Analysis (weekly) → New Rules (permanent)
```

## 🔄 Workflow

### Step 1: Export Errors to CSV

```bash
# Export last week's errors
uv run python cli.py --hours 168 --format csv --output errors.csv
```

This creates a CSV with all error details including the classification.

### Step 2: Review and Correct Classifications

Open `errors.csv` in Excel/Google Sheets and:

1. Add a new column: **`Corrected Category`**
2. For any misclassified errors, enter the correct category:
   - `INPUT_DATA_QUALITY`
   - `WORKFLOW_ENGINE`
   - `THIRD_PARTY_SYSTEM`
3. Optionally add a **`Notes`** column explaining why

**Example:**

| Job ID | Activity | Error Category | Corrected Category | Notes |
|--------|----------|----------------|-------------------|-------|
| abc123 | reading_from_s3 | THIRD_PARTY_SYSTEM | INPUT_DATA_QUALITY | S3 is our own bucket, not third-party |
| def456 | Xledger-import | INPUT_DATA_QUALITY | THIRD_PARTY_SYSTEM | Xledger API error, not data issue |

### Step 3: Import Corrections

```bash
# Import your corrections
uv run python scripts/import_corrections.py errors.csv --user your.email@example.com
```

Output:
```
INFO: Importing corrections from errors.csv...
INFO: Imported correction: THIRD_PARTY_SYSTEM → INPUT_DATA_QUALITY (job abc123...)
INFO: Imported correction: INPUT_DATA_QUALITY → THIRD_PARTY_SYSTEM (job def456...)
✅ Successfully imported 2 corrections!
INFO: These will be used as examples in future LLM classifications.
```

### Step 4: Immediate Effect - Few-Shot Learning

The next time you run analysis, the LLM will use your corrections as examples:

```bash
# Run analysis again
uv run python cli.py --hours 24
```

The LLM prompt now includes:
```
Here are some recent corrections from users:

1. Activity: reading_from_s3
   Error: An error occurred (404) when calling the HeadObject operation: Not Found
   Correct Category: INPUT_DATA_QUALITY
   Reason: S3 is our own bucket, not third-party

2. Activity: Xledger-import
   Error: GraphQL query failed
   Correct Category: THIRD_PARTY_SYSTEM
   Reason: Xledger API error, not data issue

Now classify this new error:
...
```

**Result:** Similar errors are now classified correctly! ✅

### Step 5: Weekly - Analyze Patterns

After collecting several corrections, analyze them to find patterns:

```bash
# Analyze corrections (requires 3+ similar corrections by default)
uv run python scripts/analyze_corrections.py --min-count 3
```

Output:
```
================================================================================
SUGGESTED RULES FROM USER CORRECTIONS
================================================================================

### INPUT_DATA_QUALITY
Found 2 potential rules:

1. Pattern: 'headobject' (message)
   Occurrences: 5
   Suggested rule:
   (r"headobject", "INPUT_DATA_QUALITY", "Pattern from 5 user corrections")
   Examples:
     - An error occurred (404) when calling the HeadObject operation: Not Found
     - HeadObject operation failed
     - S3 HeadObject not found

2. Pattern: 'reading_from_s3' (activity)
   Occurrences: 5
   Suggested rule:
   # Activity-specific: reading_from_s3 → INPUT_DATA_QUALITY (5 corrections)
   Examples:
     - reading_from_s3
     - reading_from_s3
     - reading_from_s3

================================================================================

💡 To add these rules:
   1. Review the suggestions above
   2. Edit src/classifier/rules.py
   3. Add appropriate patterns
   4. Test with: uv run python cli.py --hours 24 --no-llm
```

### Step 6: Add Rules (Permanent Improvement)

Based on the suggestions, update `src/classifier/rules.py`:

```python
INPUT_DATA_PATTERNS: List[Tuple[str, str]] = [
    # ... existing patterns ...
    
    # Added from user corrections (2025-12-27)
    (r"headobject.*not found", "Input file not found in S3"),
    (r"404.*headobject", "Input file missing (S3 404)"),
]
```

**Result:** These errors are now classified by rules (instant, free)! ✅

### Step 7: Test and Verify

```bash
# Test with rules only (no LLM)
uv run python cli.py --hours 24 --no-llm

# Should see: "classified by: rules" for the new patterns
```

## 📊 Benefits Over Time

### Week 1: Few-Shot Learning
- ✅ Immediate improvement
- ✅ LLM learns from 5 corrections
- ⚠️ Still uses LLM (slower, costs tokens)

### Week 2: Pattern Analysis
- ✅ System suggests 2 new rules
- ✅ You review and add to `rules.py`

### Week 3+: Rules Active
- ✅ 90% of errors classified by rules (fast, free)
- ✅ LLM only for edge cases
- ✅ System gets faster and cheaper over time

## 🛠️ Advanced Usage

### View All Corrections

```python
from src.classifier.feedback import FeedbackStore

store = FeedbackStore()
corrections = store.get_corrections(limit=10)

for c in corrections:
    print(f"{c['timestamp']}: {c['original_category']} → {c['corrected_category']}")
```

### Export for Fine-Tuning

If you want to fine-tune your own LLM model:

```python
from src.classifier.feedback import FeedbackStore

store = FeedbackStore()
store.export_for_finetuning(Path("training_data.jsonl"))
```

This creates a JSONL file in OpenAI fine-tuning format.

### Disable Few-Shot Learning

If you want to use only rules (no LLM):

```bash
uv run python cli.py --no-llm
```

Or in code:

```python
classifier = FailureClassifier(use_llm_fallback=False)
```

## 📈 Metrics

Track your improvement:

```python
from src.classifier.feedback import FeedbackStore

store = FeedbackStore()
print(f"Total corrections: {store.count()}")

# Corrections by category
for category in ['INPUT_DATA_QUALITY', 'WORKFLOW_ENGINE', 'THIRD_PARTY_SYSTEM']:
    corrections = store.get_corrections(category=FailureCategory(category))
    print(f"{category}: {len(corrections)} corrections")
```

## 🎯 Best Practices

1. **Review regularly** - Check classifications weekly
2. **Add notes** - Explain why you made the correction
3. **Be consistent** - Use the same category for similar errors
4. **Analyze patterns** - Run `analyze_corrections.py` monthly
5. **Update rules** - Add high-confidence patterns to `rules.py`
6. **Test changes** - Always test with `--no-llm` after adding rules

## 🤔 FAQ

**Q: How many corrections do I need before seeing improvement?**  
A: Few-shot learning works with just 1 correction! Pattern analysis needs 3+ similar corrections.

**Q: Will corrections slow down the classifier?**  
A: No! We only include the 5 most recent corrections in the LLM prompt.

**Q: Can I delete corrections?**  
A: Yes, edit `data/feedback.json` directly (it's just JSON).

**Q: What if I make a mistake in a correction?**  
A: Just import a new correction for the same job ID - it will override.

**Q: Do corrections affect rules-based classification?**  
A: No, rules always take priority. Corrections only affect LLM classification.

## 📁 Files

- `data/feedback.json` - Stores all corrections
- `src/classifier/feedback.py` - Feedback management code
- `scripts/import_corrections.py` - Import corrections from CSV
- `scripts/analyze_corrections.py` - Analyze patterns and suggest rules

## 🚀 Quick Start

```bash
# 1. Export errors
uv run python cli.py --format csv --output errors.csv

# 2. Edit errors.csv, add "Corrected Category" column

# 3. Import corrections
uv run python scripts/import_corrections.py errors.csv

# 4. Run analysis - LLM uses corrections as examples!
uv run python cli.py --hours 24

# 5. Weekly: analyze patterns
uv run python scripts/analyze_corrections.py

# 6. Add suggested rules to src/classifier/rules.py

# 7. Test
uv run python cli.py --hours 24 --no-llm
```

That's it! Your classifier is now self-improving! 🎉

