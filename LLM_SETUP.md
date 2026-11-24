# Optional LLM setup

The assistant's built-in commands and local fallback work without an API key.
Hosted language-model responses are optional and require a key for one of the
providers supported by `llm_engine.py`.

## Configure a provider

Copy `.env.example` to `.env` and add the key for the provider you intend to
use:

```text
OPENAI_API_KEY=...
GOOGLE_GEMINI_API_KEY=...
HUGGINGFACE_API_KEY=...
```

Install the corresponding optional SDK if required:

```bash
python -m pip install openai
python -m pip install google-generativeai
```

Hugging Face requests use the `requests` dependency in `requirements.txt`.
Only install the provider package you plan to use. Restart the application
after changing `.env`.

## Provider selection and fallback

When multiple keys are set, the current implementation selects the first
available provider in this order: OpenAI, Google Gemini, then Hugging Face.
It does not try the remaining providers if the selected provider fails; the
assistant falls back to its local pattern-based response instead.

Provider SDKs, model identifiers, and hosted endpoints can change. These
optional integrations are not covered by the automated test suite, so verify
that your provider account, SDK version, and model access are current before
relying on them. No provider key is needed to run the core assistant.

## Keep credentials private

- Keep real keys in `.env` or environment variables.
- Do not commit `.env`, paste keys into source files, or include them in logs.
- Rotate a key immediately if it is accidentally exposed.

The `.env` file is excluded by `.gitignore`; `.env.example` contains placeholders
only.
