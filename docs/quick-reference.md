# Quick Reference: Feedback Loop

## 🚀 Quick Start (5 minutes)

```bash
# 1. Export errors to CSV
uv run python cli.py --format csv --output errors.csv

# 2. Edit errors.csv in Excel/Sheets
#    Add column: "Corrected Category"
#    Fill in correct categories for misclassified errors

# 3. Import corrections
uv run python scripts/import_corrections.py errors.csv --user your@email.com

# 4. Run analysis - LLM now uses your corrections!
uv run python cli.py --hours 24
```

## 📋 Commands

### Export Errors
```bash
# Last 24 hours
uv run python cli.py --format csv --output errors.csv

# Last week
uv run python cli.py --hours 168 --format csv --output errors.csv

# Specific time range
uv run python cli.py --start-date 2025-12-20 --end-date 2025-12-27 --format csv --output errors.csv
```

### Import Corrections
```bash
# Basic import
uv run python scripts/import_corrections.py errors.csv

# With user attribution
uv run python scripts/import_corrections.py errors.csv --user john@example.com

# Verbose mode
uv run python scripts/import_corrections.py errors.csv --user john@example.com -v
```

### Analyze Patterns
```bash
# Default (requires 3+ similar corrections)
uv run python scripts/analyze_corrections.py

# Lower threshold
uv run python scripts/analyze_corrections.py --min-count 2

# Save to file
uv run python scripts/analyze_corrections.py --output suggestions.json
```

### Test Classification
```bash
# With LLM (uses few-shot learning)
uv run python cli.py --hours 24

# Rules only (no LLM)
uv run python cli.py --hours 24 --no-llm

# Verbose (see classification details)
uv run python cli.py --hours 24 -v
```

## 📊 CSV Format

### Required Columns
- `Job ID` - Unique job execution ID
- `Activity Name` - Name of the failed activity
- `Error Category` - Original classification
- `Error Message` - Error message text

### Optional Columns for Corrections
- `Corrected Category` - The correct category (add this to make corrections)
- `Notes` - Explanation of why the correction was made
- `Error Code` - HTTP status code or error code
- `Exception Type` - Exception class name

### Valid Categories
- `INPUT_DATA_QUALITY` - Data validation, format, missing fields
- `WORKFLOW_ENGINE` - Pipeline/orchestration issues
- `THIRD_PARTY_SYSTEM` - External API/service failures

## 🎯 Common Patterns

### S3 Errors
```
Error: "404 HeadObject Not Found"
Activity: "reading_from_s3"
→ INPUT_DATA_QUALITY (our bucket, missing file = data issue)
```

### External API Errors
```
Error: "GraphQL query failed"
Activity: "Xledger-import"
→ THIRD_PARTY_SYSTEM (external service)
```

### Workflow Errors
```
Error: "Activity 'foo' not found"
Activity: None
→ WORKFLOW_ENGINE (pipeline configuration)
```

## 📈 Workflow Timeline

| Time | Action | Effect |
|------|--------|--------|
| **Day 1** | Import 5 corrections | LLM uses as examples immediately |
| **Week 1** | Collect 10+ corrections | Better LLM accuracy |
| **Week 2** | Run pattern analysis | Get rule suggestions |
| **Week 2** | Add 2-3 new rules | 50% faster classification |
| **Month 1** | Add 10+ rules | 90% classified by rules (fast, free) |

## 🔍 Checking Your Progress

### View Corrections Count
```python
from src.classifier.feedback import FeedbackStore

store = FeedbackStore()
print(f"Total corrections: {store.count()}")
```

### View Recent Corrections
```python
from src.classifier.feedback import FeedbackStore

store = FeedbackStore()
recent = store.get_few_shot_examples(max_examples=5)

for ex in recent:
    print(f"{ex['activity_name']}: {ex['category']}")
    print(f"  {ex['reasoning']}")
```

### View Corrections by Category
```python
from src.classifier.feedback import FeedbackStore
from src.classifier.categories import FailureCategory

store = FeedbackStore()

for cat in FailureCategory:
    corrections = store.get_corrections(category=cat)
    print(f"{cat.value}: {len(corrections)} corrections")
```

## 🛠️ Troubleshooting

### "No corrections found"
- Make sure you added a "Corrected Category" column to your CSV
- Check that the corrected category is different from the original
- Verify the CSV file path is correct

### "Invalid category"
- Use exact category names: `INPUT_DATA_QUALITY`, `WORKFLOW_ENGINE`, `THIRD_PARTY_SYSTEM`
- Check for typos or extra spaces

### "No patterns found"
- You need at least 3 similar corrections (default)
- Try lowering the threshold: `--min-count 2`
- Collect more corrections over time

### LLM not using corrections
- Check that `use_few_shot_learning=True` (default)
- Verify corrections are in `data/feedback.json`
- Run with `-v` to see the LLM prompt

## 📁 File Locations

- **Corrections storage**: `data/feedback.json`
- **Import script**: `scripts/import_corrections.py`
- **Analysis script**: `scripts/analyze_corrections.py`
- **Rules file**: `src/classifier/rules.py`
- **Feedback code**: `src/classifier/feedback.py`

## 💡 Tips

1. **Start small** - Correct 5-10 errors to see immediate improvement
2. **Be consistent** - Use the same category for similar errors
3. **Add notes** - Explain your reasoning for future reference
4. **Review weekly** - Check classifications and add corrections
5. **Analyze monthly** - Look for patterns and add new rules
6. **Test changes** - Always test with `--no-llm` after adding rules

## 🎓 Learn More

- Full guide: [docs/feedback-loop.md](feedback-loop.md)
- Classification guide: [docs/classification-guide.md](classification-guide.md)
- Architecture: [docs/architecture.md](architecture.md)

