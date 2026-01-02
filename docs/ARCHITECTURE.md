# Architecture & Project Context

> **💡 For ChatGPT/Claude Users**:
> 1. Copy this entire file
> 2. Paste at the start of your conversation
> 3. Say: *"I'm working on ds-job-insights. Follow these guidelines."*
>
> **For Cursor/Copilot Users**: Reference with `@docs/ARCHITECTURE.md`

---

## Project Overview

AI-powered failure analysis and insights for ds-workflow-manager jobs.

## Architecture Principles

### Current Stack
- **Python 3.12+** with type hints
- **SQLAlchemy 2.0** for database access
- **Dataclasses** for data modeling (prefer over Pydantic for internal models)
- **Local LLM** via OpenAI-compatible API (Ollama/LM Studio)
- **AWS Lambda** deployment target

### Code Organization
```
src/
├── analyzer/      # Job analysis orchestration
├── classifier/    # Error classification (rules + LLM)
├── cli/          # Command-line interface
└── db/           # Database queries and connections
```

**Import Convention**:

Uses clean imports without `src.` prefix:
```python
from classifier import FailureClassifier
from db import get_db_session
```

The `src/` directory is automatically added to PYTHONPATH via:
- `pyproject.toml` configuration for pytest and mypy
- Wrapper scripts (`cli.py`) that set the path
- `uv run` commands that respect the project structure

### Key Design Patterns

1. **Hybrid Classification**: Rule-based (fast) → LLM fallback (smart)
2. **Feedback Loop**: User corrections improve LLM via few-shot learning
3. **Separation of Concerns**: 
   - `analyzer/` = orchestration
   - `classifier/` = business logic
   - `db/` = data access
   - `cli/` = presentation

### Coding Standards

- **Type hints everywhere** - No `Any` unless absolutely necessary
- **Dataclasses over dicts** - Structured data with validation
- **Context managers** - For resources (DB sessions, files)
- **Logging over print** - Use `logging` module consistently
- **Explicit over implicit** - Clear function signatures
- **Fail fast** - Validate early, raise meaningful exceptions

### Testing Philosophy

- **Unit tests** for business logic (classifier, rules)
- **Integration tests** for database queries
- **Fixtures** for test data
- **Mock external services** (LLM, AWS)

### Dependencies Management

- Use `uv` for package management
- Pin major versions, allow minor updates
- Minimize dependencies - prefer stdlib when possible

## Common Patterns

### Error Handling
```python
try:
    # Specific operation
except SpecificException as e:
    logger.error(f"Context: {e}", exc_info=True)
    raise  # or handle gracefully
```

### Database Access
```python
with get_db_session() as session:
    results = query_function(session, params)
    # Auto-commit on success, rollback on exception
```

### Configuration
```python
# Priority: ENV var → SSM Parameter → Default
value = os.getenv("KEY") or fetch_from_ssm() or DEFAULT
```

## Anti-Patterns to Avoid

❌ Mixing business logic with presentation  
❌ God classes/functions doing too much  
❌ Mutable default arguments  
❌ Bare `except:` clauses  
❌ String concatenation for SQL (use parameterized queries)  
❌ Global state (use dependency injection)  

## When Adding New Features

1. **Start with types** - Define dataclasses/protocols first
2. **Write tests** - TDD when possible
3. **Update docs** - Keep README and docstrings current
4. **Consider feedback loop** - Can users correct mistakes?
5. **Think Lambda** - Will this work in serverless environment?

