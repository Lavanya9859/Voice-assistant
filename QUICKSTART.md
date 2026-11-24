# Quick Start

## Install

Use Python 3.10 or later. From the project directory:

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS or Linux
source .venv/bin/activate
```

Install the project dependencies and start the desktop app:

```bash
python -m pip install -r requirements.txt
python gui_app.py
```

On first launch, local Whisper may download its model weights. This requires
internet access and adds startup time.

## Try a command

Type a command in the input box and press Enter. Examples:

```text
What time is it?
Open GitHub
Weather in London
Search Wikipedia for Python
```

The app also supports microphone input when a microphone is available. Voice
recognition may require internet access; typed commands remain available if
microphone setup or speech recognition is unavailable.

## Optional local security model

The assistant runs without a trained model by using its deterministic input
validator. To train a local classifier, run:

```bash
python train_model.py --output models/security_model.pkl
```

Training downloads a public dataset and requires internet access. See the
project [README](README.md) for CSV input and evaluation details.

## Troubleshooting

Run the diagnostic script for microphone and speech-recognition checks:

```bash
python diagnostic.py
```

See [Microphone troubleshooting](MICROPHONE_TROUBLESHOOTING.md) for more
details. Optional language-model configuration is documented in
[LLM setup](LLM_SETUP.md).
