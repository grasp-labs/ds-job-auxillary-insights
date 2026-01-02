# Updating Classification Rules

This guide explains how to improve the failure classifier by adding new patterns to `src/classifier/rules.py`.

## Why Update Rules?

- **Speed**: Rule-based classification is instant (no LLM call needed)
- **Cost**: Rules are free (LLM costs time/resources)
- **Consistency**: Rules always give the same result
- **Reliability**: Rules work even if LLM is unavailable

## Workflow

### 1. Run Analysis with LLM

First, analyze your failures with LLM enabled to get intelligent classifications:

```bash
# Analyze last 30 days
uv run python cli.py --hours 720 --format json --output analysis.json
```

### 2. Find Pattern Suggestions

Use the pattern analyzer to discover common patterns in LLM-classified errors:

```bash
# Analyze and suggest new patterns
uv run python scripts/analyze_patterns.py --hours 720
```

This will output something like:

```
================================================================================
THIRD_PARTY_SYSTEM
================================================================================
Total LLM-classified errors: 45

Suggested patterns to add to THIRD_PARTY_PATTERNS:

    (r"connection.*timeout", "Connection timeout - found 12x"),
    (r"rate.*limit", "Rate limit - found 8x"),
    (r"xledger.*error", "Xledger error - found 6x"),

Sample errors:

  1. Activity: fetch_xledger_data
     Reasoning: External API timeout from Xledger service
     Text: Connection timeout while calling Xledger API...
```

### 3. Add Patterns to rules.py

Edit `src/classifier/rules.py` and add the suggested patterns:

```python
THIRD_PARTY_PATTERNS: List[Tuple[str, str]] = [
    # ... existing patterns ...
    
    # Add new patterns (with descriptive reasoning)
    (r"connection.*timeout", "Connection timeout"),
    (r"rate.*limit", "Rate limit exceeded"),
    (r"xledger.*error", "Xledger API error"),
]
```

### 4. Test Your Changes

Run analysis again to verify the new patterns work:

```bash
# Run with rules only (no LLM) to test pattern matching
uv run python cli.py --hours 24 --no-llm
```

Check the output - errors that match your new patterns should now be classified by rules instead of LLM.

### 5. Iterate

Repeat this process periodically to keep improving your rules:

```bash
# Monthly: analyze last 30 days and update rules
uv run python scripts/analyze_patterns.py --hours 720 --min-count 5
```

## Pattern Writing Tips

### Good Patterns

✅ **Specific but flexible**
```python
(r"connection.*timeout", "Connection timeout")
(r"rate.*limit.*exceeded", "Rate limit exceeded")
```

✅ **Match exception types**
```python
(r"ValueError", "Value error"),
(r"KeyError", "Key error"),
```

✅ **Match provider names**
```python
(r"xledger", "Xledger API error"),
(r"visma", "Visma API error"),
```

### Bad Patterns

❌ **Too broad** (will match unrelated errors)
```python
(r"error", "Error")  # Matches everything!
(r"failed", "Failed")  # Too generic
```

❌ **Too specific** (won't match variations)
```python
(r"Connection timeout after 30 seconds", "Timeout")  # Only matches exact text
```

❌ **Hardcoded values**
```python
(r"status code 404", "Not found")  # Use (r"status.*code.*404", ...) instead
```

## Pattern Categories

### INPUT_DATA_QUALITY
Errors caused by bad/missing input data:
- Validation failures
- Missing required fields
- Wrong data format
- Type conversion errors
- Empty datasets

### THIRD_PARTY_SYSTEM
Errors from external services:
- API errors (Xledger, Visma, etc.)
- HTTP errors (4xx, 5xx)
- Connection issues
- Authentication failures
- Rate limiting

### WORKFLOW_ENGINE
Internal pipeline/orchestration issues:
- Activity not found
- Pipeline execution errors
- DAG/dependency issues
- Plugin failures
- Context/state errors

## Example: Adding a New Pattern

Let's say you notice many errors like:
```
GraphQL query failed: Field 'customer' not found in schema
```

1. **Identify the category**: This is a THIRD_PARTY_SYSTEM error (external GraphQL API)

2. **Write a pattern**:
```python
(r"graphql.*query.*failed", "GraphQL query failed"),
```

3. **Add to rules.py**:
```python
THIRD_PARTY_PATTERNS: List[Tuple[str, str]] = [
    # ... existing patterns ...
    (r"graphql.*query.*failed", "GraphQL query failed"),
]
```

4. **Test**: Run analysis and verify it matches

## Regex Syntax Reference

Common regex patterns used in rules:

- `.` - Any character
- `.*` - Zero or more of any character
- `\w+` - One or more word characters
- `\d+` - One or more digits
- `[4-5]\d{2}` - HTTP status codes 400-599
- `(?:a|b)` - Match 'a' or 'b' (non-capturing group)
- `\b` - Word boundary

All patterns are **case-insensitive** by default.

## Best Practices

1. **Start broad, then narrow**: Add general patterns first, then add specific ones
2. **Use descriptive reasoning**: Help future maintainers understand what the pattern matches
3. **Test with real data**: Always verify patterns work on actual errors
4. **Document edge cases**: Add comments for tricky patterns
5. **Review periodically**: Update rules monthly based on new error patterns

## Troubleshooting

**Pattern not matching?**
- Check if pattern is case-sensitive (it shouldn't be)
- Try simplifying the pattern (remove `.*` and test)
- Check for typos in the regex

**Pattern matching too much?**
- Make it more specific
- Add word boundaries `\b`
- Test against sample errors

**Not sure which category?**
- Run with LLM and check its reasoning
- Ask: "Is this our code or external?"
- When in doubt, use THIRD_PARTY_SYSTEM for external APIs

