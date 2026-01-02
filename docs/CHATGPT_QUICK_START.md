# ChatGPT Quick Start Guide

> **TL;DR**: Copy two files → Paste in ChatGPT → Start coding

## 🚀 3-Step Setup (30 seconds)

### Step 1: Copy These Files

Open and copy the content of these two files:

1. **[CODING_STANDARDS.md](CODING_STANDARDS.md)** ← Python best practices
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** ← Project patterns

### Step 2: Paste in ChatGPT

Start a new ChatGPT conversation and paste both files, then say:

```
I'm working on ds-job-insights, a Python project for analyzing workflow failures.
Follow these coding standards and architecture patterns for all code you generate.
```

### Step 3: Start Coding!

Now ask ChatGPT to help you:

```
"Create a new error classifier for database connection errors"
"Refactor this function to follow our standards"
"Write tests for the LLM classifier"
"Review this code for issues"
```

## 💡 Pro Tips

### Save as Custom Instructions

To avoid pasting every time:

1. Go to ChatGPT Settings → Custom Instructions
2. Paste the two files in "What would you like ChatGPT to know about you?"
3. Add: "I work on ds-job-insights. Always follow these standards."

### Use ChatGPT Projects (Plus/Team)

1. Create a new Project called "ds-job-insights"
2. Add CODING_STANDARDS.md and ARCHITECTURE.md as project files
3. All conversations in this project will automatically use these guidelines

### Quick Commands

Once setup, use these shortcuts:

- **Code Review**: "Review this against our standards"
- **Refactor**: "Refactor following our patterns"
- **New Feature**: "Create X following our architecture"
- **Tests**: "Write tests following our conventions"
- **Debug**: "Fix this bug while maintaining our standards"

## 📋 What ChatGPT Will Know

After setup, ChatGPT will automatically:

✅ Use type hints everywhere  
✅ Follow Single Responsibility Principle  
✅ Use dataclasses for structured data  
✅ Add proper error handling and logging  
✅ Write testable, maintainable code  
✅ Follow our project architecture patterns  
✅ Use context managers for resources  
✅ Avoid common anti-patterns  

## 🔄 Keep It Updated

When the team updates standards:

1. Pull latest changes: `git pull`
2. Re-copy the updated files
3. Paste in a new ChatGPT conversation
4. Or update your Custom Instructions/Project

## 📚 Full Documentation

- [CONTRIBUTING.md](../CONTRIBUTING.md) - Full development guide
- [GITHUB_COPILOT.md](GITHUB_COPILOT.md) - GitHub Copilot integration
- [README.md](../README.md) - Project overview

## ❓ Questions?

- Check [CONTRIBUTING.md](../CONTRIBUTING.md)
- Ask in team chat
- Open a discussion issue

