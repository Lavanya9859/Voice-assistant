# LLM Integration Guide

## How It Works

The Voice Assistant now supports **AI-powered natural language understanding** using Large Language Models (LLMs). This allows it to:

✅ **Understand spelling mistakes** - "waether" → recognizes as "weather"
✅ **Handle different sentence formations** - "What's the weather?" vs "Tell me weather" vs "weather details"
✅ **Answer general questions** - Questions not in the pre-defined commands
✅ **Be more conversational** - Natural responses instead of robotic ones

## Three Operation Modes

### 1. **Smart Fallback Mode** (Default - No Setup Required)
- Uses intelligent pattern matching
- No API key needed
- Works offline
- Responds to common patterns and variations

### 2. **OpenAI GPT Mode** (Recommended)
- Uses ChatGPT 3.5-turbo
- Most capable and natural responses
- Requires OpenAI API key

### 3. **Google Gemini Mode**
- Uses Google's Gemini AI
- Very capable for general questions
- Requires Google API key

### 4. **Hugging Face Mode**
- Uses open-source Llama 2 model
- Free inference API
- Requires Hugging Face token

---

## Setup Instructions

### Option A: Use Smart Fallback (No Setup)
Just run the app as-is! It will automatically use pattern matching for unknown questions.

```bash
python gui_app.py
```

### Option B: Enable OpenAI GPT (Recommended)

1. **Get OpenAI API Key:**
   - Visit: https://platform.openai.com/api-keys
   - Sign up or log in
   - Create a new API key
   - Copy the key

2. **Add to environment:**
   - Create a `.env` file in the project folder:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```
   - Or set environment variable:
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY="sk-your-api-key-here"

   # Windows CMD
   set OPENAI_API_KEY=sk-your-api-key-here
   ```

3. **Install OpenAI package:**
   ```bash
   pip install openai
   ```

4. **Run the app:**
   ```bash
   python gui_app.py
   ```

### Option C: Enable Google Gemini

1. **Get Gemini API Key:**
   - Visit: https://ai.google.dev/
   - Click "Get API key"
   - Create or select project
   - Create new API key
   - Copy the key

2. **Add to environment:**
   - Create a `.env` file:
   ```
   GOOGLE_GEMINI_API_KEY=your-api-key-here
   ```

3. **Install Google library:**
   ```bash
   pip install google-generativeai
   ```

4. **Run the app:**
   ```bash
   python gui_app.py
   ```

### Option D: Enable Hugging Face

1. **Get Hugging Face Token:**
   - Visit: https://huggingface.co/settings/tokens
   - Create a new token
   - Copy the token

2. **Add to environment:**
   - Create a `.env` file:
   ```
   HUGGINGFACE_API_KEY=hf_your-token-here
   ```

3. **Run the app:**
   ```bash
   python gui_app.py
   ```

---

## Installation

First, install the required packages:

```bash
pip install -r requirements.txt
pip install python-dotenv          # For .env file support
pip install openai                 # For OpenAI (optional)
pip install google-generativeai    # For Gemini (optional)
pip install requests               # For Hugging Face (already in requirements)
```

---

## Environment File (`.env`)

Create a `.env` file in the project root:

```bash
# Copy from .env.example
cp .env.example .env

# Edit .env and add your API keys
```

The file should look like:
```
OPENAI_API_KEY=sk-...
GOOGLE_GEMINI_API_KEY=...
HUGGINGFACE_API_KEY=hf_...
```

**Note:** The app reads keys in order: OpenAI → Gemini → Hugging Face
The first available key will be used.

---

## Testing

### Test with Smart Fallback:
```
User: hello there
Assistant: Hi there. Good evening.

User: what time is it
Assistant: The current time is 06:30 PM.

User: tell me about python
Assistant: I can help explain that! For detailed information, try searching Wikipedia or asking in a different way.
```

### Test with LLM (OpenAI):
```
User: waht is the weater
Assistant: [LLM understands misspelling and answers with weather]

User: tell me wats going on
Assistant: [Natural, conversational response]

User: what are you talking about
Assistant: I'm a personal voice assistant built with Python...
```

---

## Pricing Information

**OpenAI:**
- ~$0.002 per 1K prompt tokens
- ~$0.006 per 1K completion tokens
- Usage-based pricing

**Google Gemini:**
- Free tier: 60 requests per minute
- Paid: Starting at $0.00075 per 1K input tokens

**Hugging Face:**
- Free inference API (with rate limits)
- Paid: Depends on model and usage

**Smart Fallback:**
- ✅ FREE - No API calls, offline

---

## Troubleshooting

### LLM not responding?
1. Check if API key is correctly set:
   ```bash
   python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
   ```

2. Check internet connection

3. Verify API key is valid

4. Check API quota/credits (especially with free tiers)

### Too slow?
- Reduce context size in `llm_engine.py`
- Use OpenAI (fastest) instead of other providers
- Switch to Smart Fallback for local-only operation

### High costs?
- Switch to Hugging Face free API
- Or use Smart Fallback mode (no costs)
- Monitor usage in API dashboards

---

## How It Works Internally

```
User Input
    ↓
Speech Recognition
    ↓
Security Check
    ↓
Pattern Matching (Is it time/weather/website?)
    ↓ If YES → Direct response
    ↓ If NO  → Try LLM
    ↓
  LLM Query (if configured)
    ↓
Smart Fallback (if LLM unavailable)
    ↓
Response
    ↓
Text-to-Speech
```

---

## API Comparison

| Feature | Smart Fallback | OpenAI | Gemini | Hugging Face |
|---------|---|---|---|---|
| **Cost** | Free | $ | $ | Free |
| **Speed** | Instant | ~1-2s | ~1-2s | ~2-3s |
| **Quality** | Good | Excellent | Excellent | Good |
| **Spelling** | Limited | Excellent | Excellent | Good |
| **Offline** | Yes | No | No | No |
| **Setup** | 0 min | 5 min | 5 min | 5 min |

---

## Next Steps

1. Choose your preferred LLM provider
2. Get your API key
3. Set up `.env` file
4. Install optional packages
5. Run `python gui_app.py`
6. Test with various questions!

Enjoy your AI-powered voice assistant! 🚀
