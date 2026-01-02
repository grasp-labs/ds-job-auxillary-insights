# Output Formats Guide

This document explains the different output formats available in `ds-job-insights` and when to use each one.

## Available Formats

### 1. Text Format (Default)

**Use case:** Quick analysis, terminal output, human-readable summaries

**Command:**
```bash
uv run python cli.py --format text
```

**Features:**
- Summary statistics (total jobs, errors, time period)
- Category breakdown with percentages
- Tenant and pipeline analysis
- **Detailed error table** with all errors in tabular format
- Easy to read in terminal

**Example output:**
```
================================================================================
FAILURE ANALYSIS SUMMARY
================================================================================

Analysis Period: 2024-12-01 00:00:00 to 2024-12-31 23:59:59
Analyzed At: 2024-12-25 15:30:00

Total Failed Jobs: 156
Total Errors: 229

--------------------------------------------------------------------------------
ERRORS BY CATEGORY
--------------------------------------------------------------------------------
  INPUT_DATA_QUALITY       :   80 ( 34.9%)
  THIRD_PARTY_SYSTEM       :  100 ( 43.7%)
  WORKFLOW_ENGINE          :   49 ( 21.4%)

--------------------------------------------------------------------------------
ALL ERRORS - DETAILED BREAKDOWN
--------------------------------------------------------------------------------

Job ID     Pipeline                  Activity             Category             By     Error
----------------------------------------------------------------------------------------------------------------------------
a582e463   Watermoon - Customer      reading_from_s3      INPUT_DATA_QUALITY   rules  An error occurred (404) when calling...
a582e463   Watermoon - Customer      Xledger-import       INPUT_DATA_QUALITY   rules  DataFrame must have 'file_path' and...
...
```

### 2. Markdown Format

**Use case:** Documentation, reports, sharing with team, GitHub/Confluence

**Command:**
```bash
uv run python cli.py --format markdown --output report.md
```

**Features:**
- Professional formatted report
- Summary statistics
- Category breakdown table
- Tenant and pipeline analysis
- **Detailed error table** (markdown table format)
- Detailed error listings by category
- Ready for GitHub, Confluence, or any markdown viewer

**Example output:**
```markdown
# Failure Analysis Report

**Analysis Period:** 2024-12-01 00:00:00 to 2024-12-31 23:59:59  
**Analyzed At:** 2024-12-25 15:30:00  

## Summary

- **Total Failed Jobs:** 156
- **Total Errors:** 229

## Errors by Category

| Category | Count | Percentage |
|----------|-------|------------|
| THIRD_PARTY_SYSTEM | 100 | 43.7% |
| INPUT_DATA_QUALITY | 80 | 34.9% |
| WORKFLOW_ENGINE | 49 | 21.4% |

## All Errors - Detailed Breakdown

| Job ID | Pipeline | Activity | Category | Classified By | Error Message | Finished At |
|--------|----------|----------|----------|---------------|---------------|-------------|
| a582e463 | Watermoon - Customer | reading_from_s3 | INPUT_DATA_QUALITY | rules | An error occurred (404)... | 2024-12-25T10:30:00 |
...
```

### 3. JSON Format

**Use case:** Programmatic processing, APIs, data pipelines, custom analysis

**Command:**
```bash
uv run python cli.py --format json --output analysis.json
```

**Features:**
- Complete structured data
- All error details preserved
- Easy to parse programmatically
- Can be imported into other tools
- Includes all metadata

**Example output:**
```json
{
  "analyzed_at": "2024-12-25T15:30:00",
  "period_start": "2024-12-01T00:00:00",
  "period_end": "2024-12-31T23:59:59",
  "total_jobs": 156,
  "total_errors": 229,
  "by_category": {
    "INPUT_DATA_QUALITY": 80,
    "THIRD_PARTY_SYSTEM": 100,
    "WORKFLOW_ENGINE": 49
  },
  "results": [
    {
      "job_id": "a582e463-568a-43d7-aae1-e681ee1a97fe",
      "pipeline_name": "Watermoon - Customer created",
      "classifications": [
        {
          "category": "INPUT_DATA_QUALITY",
          "confidence": 0.9,
          "reasoning": "Input file not found in S3",
          "classified_by": "rules",
          "original_error": {
            "code": 404,
            "message": "An error occurred (404) when calling the HeadObject operation: Not Found"
          }
        }
      ]
    }
  ]
}
```

### 4. CSV Format

**Use case:** Spreadsheet analysis, Excel, Google Sheets, BI tools, pivot tables

**Command:**
```bash
uv run python cli.py --format csv --output errors.csv
```

**Features:**
- One row per error (not per job)
- All error details in columns
- Perfect for Excel/Google Sheets
- Easy filtering and sorting
- Great for pivot tables
- Import into Tableau, Power BI, etc.

**Columns:**
- `Job ID` - Unique job identifier
- `Pipeline Name` - Name of the pipeline
- `Tenant ID` - Tenant identifier
- `Finished At` - When the job finished
- `Activity Name` - Activity that failed
- `Error Category` - Classification category
- `Classified By` - How it was classified (rules/llm)
- `Confidence` - Classification confidence (0.0-1.0)
- `Reasoning` - Why it was classified this way
- `Error Code` - HTTP/error code
- `Error Message` - Full error message
- `Exception Type` - Exception class name

**Example CSV:**
```csv
Job ID,Pipeline Name,Tenant ID,Finished At,Activity Name,Error Category,Classified By,Confidence,Reasoning,Error Code,Error Message,Exception Type
a582e463-568a-43d7-aae1-e681ee1a97fe,Watermoon - Customer,tenant-123,2024-12-25T10:30:00,reading_from_s3,INPUT_DATA_QUALITY,rules,0.9,Input file not found in S3,404,An error occurred (404) when calling the HeadObject operation: Not Found,ReadException
```

## Use Case Examples

### Weekly Team Report
```bash
# Generate markdown report for last 7 days
uv run python cli.py --hours 168 --format markdown --output weekly_report.md
```

### Monthly Executive Summary
```bash
# Generate text summary for last 30 days
uv run python cli.py --hours 720 --format text > monthly_summary.txt
```

### Data Analysis in Excel
```bash
# Export to CSV for pivot table analysis
uv run python cli.py --hours 720 --format csv --output errors.csv
# Open errors.csv in Excel and create pivot tables
```

### Automated Monitoring
```bash
# Generate JSON for automated processing
uv run python cli.py --hours 24 --format json --output /tmp/daily_errors.json
# Process with custom script
python process_errors.py /tmp/daily_errors.json
```

### Slack/Email Notifications
```bash
# Generate markdown for Slack
uv run python cli.py --hours 24 --format markdown | slack-cli send --channel alerts
```

## Comparison Table

| Feature | Text | Markdown | JSON | CSV |
|---------|------|----------|------|-----|
| Human-readable | ✅ | ✅ | ❌ | ⚠️ |
| Machine-readable | ❌ | ⚠️ | ✅ | ✅ |
| Detailed error table | ✅ | ✅ | ✅ | ✅ |
| Summary statistics | ✅ | ✅ | ✅ | ❌ |
| Excel/Sheets compatible | ❌ | ❌ | ⚠️ | ✅ |
| GitHub/Confluence ready | ❌ | ✅ | ❌ | ❌ |
| Programmatic processing | ❌ | ❌ | ✅ | ⚠️ |
| Pivot tables | ❌ | ❌ | ❌ | ✅ |
| BI tools (Tableau, etc.) | ❌ | ❌ | ⚠️ | ✅ |

## Tips

1. **Use CSV for analysis** - If you need to analyze patterns, create pivot tables, or filter data, use CSV format
2. **Use Markdown for sharing** - If you're sharing with your team or documenting issues, use Markdown
3. **Use JSON for automation** - If you're building automated workflows or integrations, use JSON
4. **Use Text for quick checks** - If you just want to see what's failing, use Text format

## Combining Formats

You can generate multiple formats in one go:

```bash
# Generate all formats
uv run python cli.py --hours 720 --format json --output analysis.json
uv run python cli.py --hours 720 --format markdown --output report.md
uv run python cli.py --hours 720 --format csv --output errors.csv
```

Or use a script:
```bash
#!/bin/bash
HOURS=720
for format in json markdown csv text; do
    uv run python cli.py --hours $HOURS --format $format --output "output/analysis.$format"
done
```

