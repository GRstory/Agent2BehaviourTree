# Local LLM Setup Guide

## Using Ollama with Gemma 3

### 1. Install Ollama

**Windows/Mac/Linux:**
```bash
# Visit https://ollama.ai and download installer
# Or use curl:
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull Gemma 3 Model

```bash
# Recommended: Gemma 3 4B (4B parameters, ~2.5GB)
ollama pull gemma3:4b
```

### 3. Start Ollama Server

```bash
ollama serve
```

### 4. Run with Local Model

```bash
# Hybrid mode (RECOMMENDED): Ollama critic + Gemini generator
python runner.py --hybrid --iterations 5
# Requires: Ollama running + GEMINI_API_KEY set

# Full local: Gemma 3 4B for both critic and generator
python runner.py --ollama --iterations 5

# Or explicitly specify
python runner.py --ollama --ollama-model gemma3:4b --iterations 5
```

## Hybrid Mode (Best of Both Worlds)

**Recommended for production use!**

```bash
python runner.py --hybrid --iterations 10
```

**How it works:**
- **Critic**: Ollama Gemma 3 4B (local, fast, free)
  - Analyzes combat logs
  - Generates improvement suggestions
- **Generator**: Gemini 2.0 Flash (API, accurate)
  - Creates improved BT DSL
  - Better syntax and strategy

**Benefits:**
- ✅ Reduced API costs (only generator uses API)
- ✅ Fast critic analysis (local)
- ✅ High-quality BT generation (Gemini)
- ✅ Best cost/quality balance

**Requirements:**
- Ollama running with Gemma 3 4B
- GEMINI_API_KEY environment variable

## Model Comparison

| Mode | Critic | Generator | Speed | Quality | Cost |
|------|--------|-----------|-------|---------|------|
| **Hybrid** ⭐ | Gemma 3 4B (local) | Gemini Flash (API) | Fast | Excellent | ~$0.0005/game |
| Gemini API | Gemini Flash | Gemini Flash | Fast | Excellent | ~$0.001/game |
| Ollama | Gemma 3 4B | Gemma 3 4B | Medium | Very Good | Free |
| Mock | Mock | Mock | Instant | N/A | Free |

**Recommendation**: Use **Hybrid mode** for best results!

## Troubleshooting

### "Could not connect to Ollama"
```bash
# Make sure Ollama is running
ollama serve
```

### "Model not found"
```bash
# Pull the model first
ollama pull gemma3:4b
```

### Slow generation
- Reduce iterations
- Use GPU if available
- Use mock mode for testing

## Recommended Setup

**For production (best quality/cost):**
```bash
python runner.py --hybrid --iterations 10
# Ollama critic + Gemini generator
```

**For testing:**
```bash
python runner.py --mock --iterations 3
```

**For fully local (no API):**
```bash
python runner.py --ollama --iterations 5
# Uses Gemma 3 4B by default
```

**For best results (cloud only):**
```bash
python runner.py --iterations 10
# Uses Gemini API for both
```
