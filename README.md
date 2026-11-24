# Voice Assistant

A Python desktop assistant with a Tkinter interface for typed and spoken
commands. The project combines deterministic command routing with optional
speech recognition, text-to-speech, language-model responses, and an
experimental local input-screening model.

![Voice Assistant screenshot](image.png)

## Features

- Typed commands and microphone input
- Time, date, weather, greeting, website, and Wikipedia commands
- Text-to-speech responses
- Optional local Whisper speech recognition
- Optional LLM providers, configured through environment variables
- Deterministic input validation and an optional trained scikit-learn model

## Requirements

- Python 3.10 or later
- Internet access for weather, Wikipedia, Google speech recognition, training
  data downloads, and optional hosted LLM providers
- A working microphone for voice input; typed commands do not require one

The Whisper model weights are downloaded the first time the app initializes
local Whisper recognition. Allow extra startup time and disk space on that run.

## Run the application

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies and launch the desktop app:

```bash
python -m pip install -r requirements.txt
python gui_app.py
```

The app can run without a trained security model. In that case it uses the
deterministic validator and reports `lexical_fallback` as the decision source.
To train and save the optional local model:

```bash
python train_model.py --output models/security_model.pkl
```

The default training command downloads a public prompt-injection dataset and
therefore requires internet access. You can also supply a CSV with `text` and
`label` columns:

```bash
python train_model.py --csv data/prompt_injection.csv --output models/security_model.pkl
```

Model artifacts and evaluation reports are local outputs and are excluded from
version control.

## Configuration

Copy `.env.example` to `.env` to configure an optional LLM provider. Keep real
API keys in `.env` or environment variables; never commit them. See
[LLM setup](LLM_SETUP.md) for provider-specific notes.

## Tests

Run the automated security regression tests with:

```bash
python -m unittest discover -s tests -v
```

The microphone scripts in the repository are manual hardware diagnostics and
are not part of this automated test suite.

## Project layout

| Path | Purpose |
| --- | --- |
| `assistant_core.py` | Command routing, weather lookup, and assistant responses |
| `gui_app.py` | Tkinter desktop interface |
| `secure_assistant.py` | Deterministic input validation |
| `ml_security_engine.py` | Optional local model inference and policy decisions |
| `train_model.py` | Dataset loading, training, calibration, and evaluation |
| `llm_engine.py` | Optional provider-backed responses and local fallback |
| `whisper_recognizer.py` | Speech recognition integration |
| `tests/` | Automated regression tests |
| `diagnostic.py`, `check_audio.py`, `advanced_mic_test.py`, `test_voice.py` | Manual microphone diagnostics |
| `pdtrain.yaml` | External training configuration; not read by the local trainer |

## Limitations

This is a learning and portfolio project, not a production security boundary.
The validator and classifier can produce false positives and false negatives;
they do not replace authorization, sandboxing, or human review. Only load
serialized model files produced by a trusted training process.
Optional hosted LLM integrations depend on external SDKs and model availability
and are not covered by the automated tests.

For microphone setup, see [Microphone troubleshooting](MICROPHONE_TROUBLESHOOTING.md).
For a short run-through, see the [Quick Start](QUICKSTART.md).
