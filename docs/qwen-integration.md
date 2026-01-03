# Qwen LLM Integration

This project supports using Qwen models for intelligent error classification via vLLM.

## Quick Start

### 1. Configure Environment

Create or update `.env`:

```bash
# LLM Configuration - Using local Qwen model via vLLM
LOCAL_LLM_MODEL=Qwen/Qwen3-4B-Instruct-2507-FP8
LOCAL_LLM_BASE_URL=http://172.30.50.101:8000/v1
LOCAL_LLM_API_KEY=not-needed
```

### 2. Test the Integration

```bash
# Run the test script
PYTHONPATH=src python scripts/test_qwen_llm.py
```

Expected output:
```
✅ All tests passed! Qwen LLM is ready to use.
```

### 3. Use in Analysis

```bash
# Use with default settings from .env
python cli.py --hours 24

# Or specify explicitly
python cli.py --llm-model Qwen/Qwen3-4B-Instruct-2507-FP8 \
              --llm-url http://172.30.50.101:8000/v1
```

## How It Works

The classifier uses a **two-stage approach**:

1. **Rule-based** (fast, deterministic)
   - Pattern matching for known error types
   - HTTP status code heuristics
   - Keyword detection

2. **LLM fallback** (intelligent, adaptive)
   - Used when rules don't match
   - Qwen model analyzes error context
   - Returns category + confidence + reasoning

### Example Classification

**Input error:**
```json
{
  "code": null,
  "message": "The customer data export job encountered an unusual condition",
  "exception": "CustomProcessingException"
}
```

**Qwen's response:**
```
Category: WORKFLOW_ENGINE
Confidence: 0.8
Reasoning: The CustomProcessingException indicates an internal pipeline issue
```

## vLLM Server Setup

If you need to set up your own vLLM server:

### 1. Install vLLM

```bash
pip install vllm
```

### 2. Download Qwen Model

```bash
# Using Hugging Face
huggingface-cli download Qwen/Qwen3-4B-Instruct-2507-FP8
```

### 3. Start vLLM Server

```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-4B-Instruct-2507-FP8 \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype auto \
    --max-model-len 8192
```

### 4. Verify Server

```bash
curl http://localhost:8000/v1/models
```

## Supported Models

Any OpenAI-compatible model works. Examples:

| Model | Size | Use Case |
|-------|------|----------|
| `Qwen/Qwen3-4B-Instruct-2507-FP8` | 4B | Fast, good quality |
| `Qwen/Qwen2.5-7B-Instruct` | 7B | Better accuracy |
| `llama3.2:3b` (Ollama) | 3B | Quick local testing |
| `mistral:7b` (Ollama) | 7B | Alternative option |

## Configuration Options

### Environment Variables

```bash
# Model name (must match vLLM server)
LOCAL_LLM_MODEL=Qwen/Qwen3-4B-Instruct-2507-FP8

# API endpoint
LOCAL_LLM_BASE_URL=http://172.30.50.101:8000/v1

# API key (not needed for local vLLM)
LOCAL_LLM_API_KEY=not-needed
```

### CLI Arguments

```bash
# Disable LLM (rules only)
python cli.py --no-llm

# Use different model
python cli.py --llm-model Qwen/Qwen2.5-7B-Instruct

# Use different endpoint
python cli.py --llm-url http://localhost:8000/v1
```

## Troubleshooting

### Connection Refused

```
❌ Cannot connect to local LLM at http://172.30.50.101:8000/v1
```

**Solution:**
1. Check vLLM server is running: `curl http://172.30.50.101:8000/v1/models`
2. Verify network connectivity
3. Check firewall settings

### Model Not Found

```
❌ Model 'Qwen/Qwen3-4B-Instruct-2507-FP8' not found
```

**Solution:**
1. List available models: `curl http://172.30.50.101:8000/v1/models`
2. Update `LOCAL_LLM_MODEL` to match exactly

### Slow Response

**Solution:**
- Use smaller model (3B instead of 7B)
- Reduce `max_tokens` in classifier code
- Use GPU acceleration for vLLM

## Performance

| Model | Speed | Accuracy | Memory |
|-------|-------|----------|--------|
| Qwen3-4B-FP8 | ~2s/request | High | ~4GB |
| Qwen2.5-7B | ~4s/request | Higher | ~8GB |
| Rules only | <0.1s | Good | Minimal |

**Recommendation:** Use rules + Qwen3-4B for best balance.

## Next Steps

- ✅ Test integration: `python scripts/test_qwen_llm.py`
- ✅ Run analysis: `python cli.py --hours 24`
- 📝 Add corrections: See `docs/feedback-loop.md`
- 🔧 Fine-tune: Export corrections for training

