# ds-job-insights

AI-powered failure analysis and insights for ds-workflow-manager jobs.

## Overview

This service analyzes failed job executions from ds-workflow-manager and classifies failures into categories:

- **INPUT_DATA_QUALITY** - Data validation failures, missing fields, format issues, schema mismatches
- **WORKFLOW_ENGINE** - Internal pipeline/activity execution issues, DAG errors, SQL binding errors
- **THIRD_PARTY_SYSTEM** - External API failures (Xledger, Ivalua), timeouts, auth issues

The service connects to the PostgreSQL database using credentials from AWS SSM Parameter Store (`/dsw/mgr/db_uri-{env}`) and analyzes the `job_execution` table's `status` and `data` columns to extract and classify error information.

## Architecture

```
┌──────────────────┐     ┌──────────────────────┐     ┌───────────────────┐
│  EventBridge     │────▶│  FailureAnalyzerJob  │────▶│  Analysis Results │
│  (Daily trigger) │     │  (Lambda)            │     │  (S3/Slack/DB)    │
└──────────────────┘     └──────────────────────┘     └───────────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │  ds-workflow-manager │
                         │  PostgreSQL DB       │
                         └──────────────────────┘
```

## Classification Approach

The classifier uses a **hybrid approach** that improves over time:

1. **Rule-based** (fast, free, deterministic) - Pattern matching for known error types
2. **LLM with Few-Shot Learning** (smart, learns from corrections) - Uses local LLM via OpenAI-compatible API
   - **Ollama** (default) - `http://localhost:11434/v1`
   - **LM Studio** - `http://localhost:1234/v1`
   - **Any OpenAI-compatible endpoint** - vLLM, LocalAI, etc.
3. **Feedback Loop** (self-improving) - Learns from your corrections

### 🔄 Improving Classification (Recommended Workflow)

The classifier gets better over time as you correct misclassifications:

```bash
# 1. Export errors to CSV
uv run python cli.py --format csv --output errors.csv

# 2. Edit errors.csv: Add "Corrected Category" column for any misclassifications

# 3. Import corrections - LLM immediately uses them as examples!
uv run python scripts/import_corrections.py errors.csv --user your@email.com

# 4. Weekly: Analyze patterns and get rule suggestions
uv run python scripts/analyze_corrections.py --min-count 3

# 5. Add suggested rules to src/classifier/rules.py for permanent improvement
```

**Result:** The classifier learns from your corrections and gets faster/cheaper over time!

📖 **Full guide:** [docs/feedback-loop.md](docs/feedback-loop.md) | [Quick Reference](docs/quick-reference.md)

### Alternative: Pattern Analysis (Discover Patterns from Data)

You can also analyze existing errors to discover patterns:

```bash
# Analyze last 30 days and suggest new patterns
uv run python scripts/analyze_patterns.py --hours 720

# Show top 20 patterns per category
uv run python scripts/analyze_patterns.py --hours 720 --top 20

# Only suggest patterns that appear at least 5 times
uv run python scripts/analyze_patterns.py --hours 720 --min-count 5
```

This will analyze errors that were classified by LLM and suggest regex patterns to add to `rules.py`. Once you add these patterns, those errors will be classified instantly without needing the LLM.

**See [docs/updating-rules.md](docs/updating-rules.md) for a complete guide on updating classification rules.**

## Installation

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install dev dependencies
uv sync --dev

# Configure environment (optional)
cp .env.example .env
# Edit .env with your database and LLM settings
```

### LLM Setup (Ollama)

The tool uses local LLM for intelligent error classification:

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
brew services start ollama

# Pull a model (choose one)
ollama pull llama3.2:3b    # Fastest, 2GB (default, recommended for testing)
ollama pull qwen2.5:7b     # Best accuracy, 4.7GB (recommended for production)
ollama pull mistral        # Balanced, 4.1GB
ollama pull llama3.1:8b    # High accuracy, 4.7GB

# Verify installation
ollama list
```

**Alternative: LM Studio**
- Download from [lmstudio.ai](https://lmstudio.ai/)
- Load any model
- Start local server (default: `http://localhost:1234/v1`)
- Use `--llm-url http://localhost:1234/v1`

## Usage

### As a Lambda function

```python
from src.analyzer import FailureAnalyzerJob

def handler(event, context):
    job = FailureAnalyzerJob(use_llm=True)
    summary = job.run()
    return summary.to_dict()
```

### CLI (local testing)

The CLI provides a convenient way to run failure analysis locally.

```bash
# Analyze last 24 hours with local LLM (Ollama)
uv run python cli.py

# Analyze last 30 days, rules only (fastest, no LLM)
uv run python cli.py --hours 720 --no-llm

# Use a different model
uv run python cli.py --llm-model qwen2.5:7b

# Use LM Studio instead of Ollama
uv run python cli.py --llm-url http://localhost:1234/v1

# Analyze specific time range
uv run python cli.py --since "2024-12-01 00:00:00" --until "2024-12-31 23:59:59"

# Filter by tenant ID
uv run python cli.py --tenant-id "67791af9-750d-4697-a9d4-2d69a4a9405a"

# Output as JSON for further processing
uv run python cli.py --format json --output analysis.json

# Export to CSV for spreadsheet analysis
uv run python cli.py --format csv --output errors.csv

# Generate markdown report
uv run python cli.py --format markdown --output report.md

# Verbose logging for debugging
uv run python cli.py --verbose

# Show all available options
uv run python cli.py --help
```

**Example Output (with local LLM):**
```
================================================================================
FAILURE ANALYSIS SUMMARY
================================================================================

Analysis Period: 2025-11-21T20:03:06+00:00 to 2025-12-21T20:03:06+00:00
Analyzed At: 2025-12-21T20:03:06+00:00

Total Failed Jobs: 156
Total Errors: 229

--------------------------------------------------------------------------------
ERRORS BY CATEGORY
--------------------------------------------------------------------------------
  THIRD_PARTY_SYSTEM       :  100 ( 43.7%)  ← LLM classified S3, API errors
  INPUT_DATA_QUALITY       :   80 ( 34.9%)  ← LLM classified schema issues
  WORKFLOW_ENGINE          :   49 ( 21.4%)  ← LLM classified binding errors

--------------------------------------------------------------------------------
FAILED JOBS BY TENANT
--------------------------------------------------------------------------------
  eae3b2be-f377-445e-86b0-ead33827daae: 105 jobs
  67791af9-750d-4697-a9d4-2d69a4a9405a: 36 jobs
  ...

--------------------------------------------------------------------------------
FAILED JOBS BY PIPELINE
--------------------------------------------------------------------------------
  G8:: PO - Eviny Fornybar AS (44660227): 54 jobs
  Watermoon - Customer created: 36 jobs
  G8 :: Supplier: 19 jobs
  ...
```

### Programmatic API

```python
from src.analyzer import FailureAnalyzerJob
from datetime import datetime, timedelta, timezone

# Initialize analyzer
analyzer = FailureAnalyzerJob(
    use_llm=False,  # Set to True for LLM classification
    lookback_hours=24,
)

# Run analysis
summary = analyzer.run()

# Access results
print(f"Total failed jobs: {summary.total_jobs}")
print(f"Total errors: {summary.total_errors}")
print(f"By category: {summary.by_category}")

# Analyze specific time range
since = datetime.now(timezone.utc) - timedelta(days=7)
summary = analyzer.run(since=since)

# Filter by tenant
from uuid import UUID
tenant_id = UUID("67791af9-750d-4697-a9d4-2d69a4a9405a")
summary = analyzer.run(tenant_id=tenant_id)

# Export to JSON
import json
with open("results.json", "w") as f:
    json.dump(summary.to_dict(), f, indent=2, default=str)
```

See [`examples/analyze_failures.py`](examples/analyze_failures.py) for more examples.

### Output Formats

The CLI supports multiple output formats for different use cases:

#### 1. Text Format (Default)
Human-readable summary with statistics and detailed error table:
```bash
uv run python cli.py --format text
```

#### 2. Markdown Format
Comprehensive reports for documentation or sharing:
```bash
uv run python cli.py --format markdown --output report.md
```

#### 3. JSON Format
Machine-readable format for further processing:
```bash
uv run python cli.py --format json --output analysis.json
```

#### 4. CSV Format
Spreadsheet-compatible format for analysis in Excel, Google Sheets, etc.:
```bash
uv run python cli.py --format csv --output errors.csv
```

**CSV columns include:**
- Job ID, Pipeline Name, Tenant ID, Finished At
- Activity Name, Error Category, Classified By, Confidence
- Reasoning, Error Code, Error Message, Exception Type

Perfect for pivot tables, filtering, and importing into BI tools!

### Report Contents

All formats (except CSV) include:
- **Summary statistics** - Total jobs, errors, time period
- **Category breakdown** - Errors grouped by INPUT_DATA_QUALITY, THIRD_PARTY_SYSTEM, WORKFLOW_ENGINE
- **Tenant analysis** - Failed jobs per tenant
- **Pipeline analysis** - Top failing pipelines
- **Detailed error table** - All errors with job ID, pipeline, activity, category, classification method, and error message
- **Detailed error listings** - Individual job failures with:
  - Job ID, pipeline name, timestamp
  - Error classifications with confidence scores
  - LLM reasoning for each classification
  - Original error messages and exceptions

Example report structure:
```markdown
# Failure Analysis Report

## Summary
- Total Failed Jobs: 156
- Total Errors: 229

## Errors by Category
| Category | Count | Percentage |
|----------|-------|------------|
| THIRD_PARTY_SYSTEM | 100 | 43.7% |
| INPUT_DATA_QUALITY | 80 | 34.9% |
| WORKFLOW_ENGINE | 49 | 21.4% |

## Detailed Error Analysis
### THIRD_PARTY_SYSTEM (92 jobs)
#### Job: `a582e463-568a-43d7-aae1-e681ee1a97fe`
- Pipeline: Watermoon - Customer created
- Errors:
  1. **SUBMIT :: Xledger**
     - Category: `THIRD_PARTY_SYSTEM`
     - Confidence: 0.90
     - Reasoning: Xledger API returned a 404 Not Found error
     - Exception: `ReadException`
     - Message: An error occurred (404) when calling the HeadObject operation: Not Found
```

### Direct Classifier API

```python
from src.classifier import FailureClassifier

classifier = FailureClassifier(use_llm_fallback=False)

result = classifier.classify({
    "code": 500,
    "message": "Xledger API timeout after 30 seconds",
    "exception": "ReadTimeout",
    "details": {},
})

print(result.category)  # THIRD_PARTY_SYSTEM
print(result.reasoning)  # "Xledger API error"
print(result.confidence)  # 0.9
```

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src

# Lint
uv run ruff check src tests

# Type check
uv run mypy src
```

## Database Connection

The service connects to the `ds-workflow-manager` PostgreSQL database to query failed job executions.

### Configuration Priority

The database connection is configured in the following priority order:

1. **Full URI** - `DATABASE_URI` environment variable
   ```bash
   export DATABASE_URI="postgresql://user:pass@host:5432/dbname"
   ```

2. **Individual Components** - Separate environment variables
   ```bash
   export DB_HOST="localhost"
   export DB_PORT="5432"  # optional, defaults to 5432
   export DB_NAME="workflow_manager"
   export DB_USER="postgres"
   export DB_PASSWORD="secret"
   ```

3. **AWS SSM Parameter Store** - `/dsw/mgr/db_uri-{BUILDING_MODE}`
   - Requires AWS credentials and IAM permissions
   - Used in production/staging environments

### Query Details
```sql
SELECT je.id, je.pipeline_id, je.tenant_id, je.status, je.data, je.finished_at
FROM job_execution je
WHERE je.status = 'FAILURE'
  AND je.data IS NOT NULL
  AND je.data->>'run_info' IS NOT NULL
  AND je.finished_at >= :since
  AND je.finished_at <= :until
ORDER BY je.finished_at DESC
```

The `data` column contains a JSON object with error information in `data.run_info.errors[]`.

## Environment Variables

### Database Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URI` | Full PostgreSQL connection string | SSM lookup |
| `DB_HOST` | Database host | - |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | - |
| `DB_USER` | Database user | - |
| `DB_PASSWORD` | Database password | - |
| `BUILDING_MODE` | Environment (dev/staging/prod) for SSM lookup | `dev` |
| `AWS_REGION` | AWS region for SSM | `eu-north-1` |

### LLM Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LOCAL_LLM_MODEL` | LLM model name | `llama3.2:3b` |
| `LOCAL_LLM_BASE_URL` | LLM API URL (OpenAI-compatible) | `http://localhost:11434/v1` |
| `LOCAL_LLM_API_KEY` | API key (if required) | `not-needed` |

## Common Error Patterns

Based on analysis of production data, here are the most common failure patterns:

### INPUT_DATA_QUALITY (26.5%)
- `InvalidInputException`: Empty DataFrames, missing columns
- `ConversionException`: Type conversion errors (e.g., string to INT)
- `ParserException`: SQL syntax errors in user queries
- `DatasetException`: Schema validation failures
- `ValueError`: Invalid pandas DataFrame operations

### THIRD_PARTY_SYSTEM (15.8%)
- `UnhandledXledgerException`: Xledger API validation errors
- `GraphQLException`: Xledger GraphQL query failures
- `HTTPError`: 503 Service Unavailable from Ivalua
- `TimeoutError`: FTP connection timeouts
- `AuthenticationError`: SOAP authentication failures

### WORKFLOW_ENGINE (7.3%)
- `BinderException`: SQL column not found errors
- `WriteException`: Internal server errors
- `ReadException`: Internal read operation failures

### UNKNOWN (50.4%)
- S3 HeadObject 404 errors (needs classification rule or LLM)
- Various edge cases that don't match existing patterns
- **Recommendation:** Enable LLM classification to reduce UNKNOWN category

## Development

### AI-Assisted Development

This project includes AI instructions for consistent code generation.

**For ChatGPT/Claude users** (most common):
1. Copy [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
2. Paste at start of conversation
3. Say: "Follow these guidelines"

**For GitHub Copilot users**: See [docs/GITHUB_COPILOT.md](docs/GITHUB_COPILOT.md)

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development guide.

### Code Quality Tools

```bash
# Type checking
uv run mypy src/

# Linting
uv run ruff check src/

# Tests
uv run pytest tests/
```

## License

Proprietary - Grasp Labs
