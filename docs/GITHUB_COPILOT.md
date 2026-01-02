# GitHub Copilot Integration Guide

This guide shows how to use GitHub Copilot effectively with this project's coding standards.

## 🎯 TL;DR

**You don't need to add comments to every file!**

GitHub Copilot runs locally and learns from your existing codebase automatically. Just:
1. ✅ Keep your existing code clean and consistent
2. ✅ Review Copilot suggestions against our standards
3. ✅ Use inline comments only for complex/unusual cases

That's it!

## 📁 Documentation Files

- **[CODING_STANDARDS.md](CODING_STANDARDS.md)** - Python best practices and principles
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Project architecture, patterns, and conventions
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Development workflow and standards
- **[CHATGPT_QUICK_START.md](CHATGPT_QUICK_START.md)** - For ChatGPT users

## 🔄 Using These Standards in Other Repos

### Quick Setup for Existing Projects

**Step 1**: Copy the generic standards (same for all Python projects):

```bash
# From this repo to your other repo
cp docs/CODING_STANDARDS.md /path/to/other-repo/docs/
cp docs/CHATGPT_QUICK_START.md /path/to/other-repo/docs/
cp docs/GITHUB_COPILOT.md /path/to/other-repo/docs/
```

**Step 2**: Create project-specific `ARCHITECTURE.md`:

```bash
# Customize for your project's tech stack and patterns
vim /path/to/other-repo/docs/ARCHITECTURE.md
```

**Step 3**: Create/update `CONTRIBUTING.md`:

```bash
# Add project-specific setup and workflow
vim /path/to/other-repo/CONTRIBUTING.md
```

### What to Keep Generic vs Customize

**Keep the same across all repos** (copy as-is):
- ✅ `CODING_STANDARDS.md` - Python best practices don't change
- ✅ `CHATGPT_QUICK_START.md` - Instructions are universal
- ✅ `GITHUB_COPILOT.md` - This file

**Customize per project**:
- 🔧 `ARCHITECTURE.md` - Tech stack, patterns, project structure
- 🔧 `CONTRIBUTING.md` - Setup, testing, deployment workflow

### Keeping Standards Updated

When you improve standards in one repo, sync to others:

```bash
#!/bin/bash
# sync-standards.sh
REPOS=("api-service" "data-pipeline" "ml-training")
SOURCE="ds-job-insights"

for repo in "${REPOS[@]}"; do
  echo "Syncing standards to $repo..."
  cp $SOURCE/docs/CODING_STANDARDS.md ../$repo/docs/
  cp $SOURCE/docs/CHATGPT_QUICK_START.md ../$repo/docs/
  cp $SOURCE/docs/GITHUB_COPILOT.md ../$repo/docs/
done
```

## 🤖 Using GitHub Copilot

**Good news**: GitHub Copilot runs **locally in your IDE** and learns from your existing codebase. You **don't need to add comments to every file**!

### How Copilot Learns (Automatic)

Copilot automatically learns from:

1. ✅ **Your existing code patterns** (most important!)
   - If your codebase uses type hints, Copilot will too
   - If you use dataclasses, Copilot suggests dataclasses
   - If you use context managers, Copilot follows that pattern

2. ✅ **Open files in your editor**
   - Keep `docs/CODING_STANDARDS.md` open → Copilot sees it
   - Open related files → Copilot understands context

3. ✅ **File structure and naming**
   - Consistent naming helps Copilot understand intent
   - Clear module organization guides suggestions

### When to Add Comments (Optional)

Only add comments for **unusual or complex cases**:

#### Inline Comments (When Needed)

Guide Copilot with specific comments:

```python
# Create a dataclass following our standards (type hints, to_dict method)
@dataclass
class ErrorClassification:
    # Copilot will suggest fields with type hints

# Add error handling following our patterns (specific exception, logging)
try:
    # Copilot will suggest implementation
```

### Method 3: Consistent Patterns

Copilot learns from existing code. Our codebase already follows these patterns:

**Dataclasses with type hints:**
```python
@dataclass
class AnalysisResult:
    job_id: str
    classifications: list[ClassifiedFailure]

    def to_dict(self) -> dict[str, Any]:
        return {...}
```

**Context managers for resources:**
```python
with get_db_session() as session:
    results = get_failed_jobs(session, since=since)
```

**Specific error handling:**
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Failed to process {item_id}: {e}", exc_info=True)
    raise
```

## 💡 Best Practices

### DO:
✅ **Keep existing code clean** - Copilot mimics what it sees (most important!)
✅ **Use consistent naming** - Copilot learns from patterns
✅ **Review suggestions** - Check against our standards
✅ **Open related files** - Gives Copilot more context
✅ **Add comments for complex logic** - Only when needed

### DON'T:
❌ **Add comments to every file** - Not needed, Copilot learns from code
❌ **Accept suggestions blindly** - Always review
❌ **Accept code without type hints** - Our standard requires them
❌ **Accept bare `except:` clauses** - Use specific exceptions
❌ **Accept mutable default arguments** - Common Python pitfall
❌ **Accept god classes/functions** - Keep it simple

## 🔍 Review Checklist

Before accepting Copilot suggestions, verify:

- [ ] Type hints on all parameters and return values
- [ ] Docstrings for public functions (Google style)
- [ ] Specific exception handling (not bare `except:`)
- [ ] Logging instead of print statements
- [ ] Context managers for resources
- [ ] Single Responsibility Principle
- [ ] No mutable default arguments
- [ ] Follows existing code patterns

## 📚 Quick Reference

### Our Key Patterns

**Configuration (ENV → SSM → Default):**
```python
model = os.getenv("LOCAL_LLM_MODEL", "llama3.2:3b")
```

**Database Access:**
```python
with get_db_session() as session:
    results = query_function(session, params)
```

**Error Classification:**
```python
# Rule-based first, LLM fallback
result = self._classify_by_rules(text, code)
if not result and self.use_llm_fallback:
    result = self._classify_with_llm(error, activity)
```

## 🔄 Updating Standards

When you discover new patterns:

1. Update [CODING_STANDARDS.md](CODING_STANDARDS.md) or [ARCHITECTURE.md](ARCHITECTURE.md)
2. Commit: `git commit -m "docs: Add pattern for X"`
3. Share in code review
4. Copilot will learn from the new code

## 📖 Full Documentation

- [CODING_STANDARDS.md](CODING_STANDARDS.md) - Complete Python standards
- [ARCHITECTURE.md](ARCHITECTURE.md) - Project architecture
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development workflow
- [CHATGPT_QUICK_START.md](CHATGPT_QUICK_START.md) - For ChatGPT users
