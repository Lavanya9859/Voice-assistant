# Voice Assistant

A Python-based voice assistant with a Tkinter desktop interface and a local ML security layer. It supports typed commands, microphone input, text-to-speech replies, basic web shortcuts, Wikipedia summaries, live weather lookup, and adversarial prompt-injection detection.

![Voice Assistant screenshot](image.png)

## Project Summary

This project implements a hybrid command-processing architecture: deterministic routing handles ordinary assistant capabilities, while a CPU-efficient local machine-learning security gate evaluates untrusted text before command execution. The security pipeline combines word and character TF-IDF features with balanced Logistic Regression, a deterministic structural validator, configurable thresholding, adversarial robustness evaluation, and runtime telemetry. The design prioritizes local processing, reproducibility, and auditable security decisions.

## Key Features

- Speech recognition for voice commands
- Text-to-speech responses
- Tkinter GUI with typed input and continuous listening
- Website shortcuts for common platforms
- Time, date, weather, and greeting responses
- Wikipedia summaries for quick information lookup
- Local ML security gate for prompt injection and malicious command intent
- Security telemetry: threat probability, latency, decision, and inference source

## Tech Stack

- Python
- Tkinter
- SpeechRecognition
- pyttsx3
- PyAudio
- wikipedia
- Open-Meteo API
- scikit-learn
- joblib

## Project Structure

- `assistant_core.py` - main assistant logic and command handling
- `gui_app.py` - Tkinter desktop application
- `secure_assistant.py` - deterministic regex and sanitization baseline
- `ml_security_engine.py` - local inference and fail-closed policy boundary
- `train_model.py` - reproducible TF-IDF + Logistic Regression trainer
- `requirements.txt` - package dependencies
- `image.png` - project screenshot

## Setup

1. Create and activate a virtual environment.
2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Train the free local security model:

   ```bash
   python train_model.py --output models/security_model.pkl
   ```

   The default trainer downloads the open `deepset/prompt-injections` dataset
   through the public Hugging Face Datasets Server. This requires no account
   or API key. The legacy UCI SMS corpus is available only as an explicit
   proxy baseline with `--uci-baseline`; it should not support claims about
   prompt-injection detection.

   You can provide a domain-specific CSV instead:

   ```bash
   python train_model.py --csv data/prompt_injection.csv --output models/security_model.pkl
   ```

   The CSV must contain `text` and `label` columns. Accepted labels include
   `benign`, `ham`, `safe`, `malicious`, `spam`, `injection`, and `attack`.

   Training prints a classification report, ROC-AUC, average precision, a
   threshold calibrated on a separate split, and a deterministic perturbation
   evaluation. It also writes a machine-readable report to
   `reports/security_evaluation.json`, including duplicate handling and
   word-only, character-only, and combined-feature ablations. The default
   `--max-fnr 0.02` constrains the calibration
   false-negative rate to at most two percent where the calibration sample
   permits a feasible threshold.

4. Run the desktop app:

   ```bash
   python gui_app.py
   ```

## Example Commands

- `time` - tells the current time
- `date` - tells the current date
- `open youtube` - opens YouTube
- `open google` - opens Google
- `open github` - opens GitHub
- `open leetcode` - opens LeetCode
- `search wikipedia python` - shows a short Wikipedia summary
- `weather in london` - gets the current weather for London
- `show weather for delhi` - gets the current weather for Delhi
- `exit` or `quit` - closes the assistant

## Notes for Use

- The assistant uses deterministic command routing together with a local TF-IDF and Logistic Regression security classifier; no commercial AI inference API is required.
- Microphone input requires `SpeechRecognition` and `PyAudio`.
- Weather lookup needs internet access because it uses the Open-Meteo API.
- If voice input is not available, the text box still works.
- If the model artifact is unavailable, the application uses the deterministic
   regex validator and labels telemetry as `lexical_fallback`.

## ML Security Design

The security boundary runs before command routing for both typed and
recognized speech. This **Fail-Closed System Topology** combines word TF-IDF
bigrams with character TF-IDF 3-to-5-grams, then applies balanced Logistic
Regression locally on the CPU. Character features preserve evidence across
inserted spaces and punctuation.

The constructor default decision threshold is `0.70`; a trained artifact can
replace it with a threshold selected through **Precision-Recall Optimization**
under an explicit false-negative-rate constraint. Inputs matching the
deterministic baseline are blocked immediately; model probability at or above
the calibrated threshold is also blocked. Model loading or inference failures
fail closed. The GUI logs the decision, probability percentage, processing
latency, and inference source for each turn.

When a trained artifact contains a calibrated threshold, it overrides the
constructor default. Blocked model decisions include the highest positive
linear TF-IDF feature contributions as **Post-Hoc Feature Attribution**
evidence, while regex-blocked inputs report the matched structural rule. This
is local model evidence, not a causal explanation.

The trainer performs **Adversarial Robustness Evaluation** using deterministic
perturbations, including whitespace insertion, zero-width characters, and
leetspeak substitutions. Clean and perturbed test performance must be
reported separately; strong clean-set scores do not establish robustness
against adaptive or distribution-shifted attacks.

The UCI SMS corpus is only a baseline proxy and should not support claims
about general prompt-injection robustness. For an internship-quality study,
create a labeled CSV from freely accessible prompt-injection datasets on
Kaggle or UCI, define a taxonomy such as `benign`, `instruction_override`,
`system_prompt_exfiltration`, `shell_injection`, and `sql_injection`, and use
an untouched assistant-specific test split. Report class-wise precision,
recall, F1, macro-F1, confusion matrices, threshold curves, and latency.

The serialized scikit-learn artifact is loaded with `joblib`. Only load model
files generated by your own trusted training process; serialized Python
objects are not safe to load from untrusted sources.

## Empirical Security Contribution & Research Value

This repository presents an empirical, locally deployable security prototype
for an interactive command interface. Its research value is grounded in:

- a working desktop interface with typed and speech-mediated inputs
- structural data lineage from dataset source through feature extraction,
   calibration, serialization, and runtime enforcement
- a deterministic validator baseline for interpretable attack interception
- combined word and character n-gram modeling for lexical and obfuscation-aware
   signal capture
- **Precision-Recall Optimization** with an explicit false-negative error
   boundary
- **Adversarial Robustness Evaluation** on deterministic input perturbations
- **Post-Hoc Feature Attribution** for auditable local model evidence
- **Fail-Closed System Topology** for model absence, loading failure, and
   inference failure
- reproducible CPU-based experimentation with `random_state=42`

The UCI SMS corpus is retained only as an explicitly identified proxy baseline;
the default training path uses an open prompt-injection dataset. Publication-
quality claims still require domain-specific labels, duplicate controls,
versioned data provenance, untouched test data, confidence intervals, and
evaluation against adaptive attackers.

## Reproducible evaluation

The training command uses a fixed random seed (`42`), removes exact
case/whitespace duplicates before splitting, keeps separate fit, calibration,
and test partitions, and writes JSON metrics. The report contains accuracy,
class-wise precision/recall/F1, macro-F1, confusion matrices, ROC-AUC, average
precision, and ablations for word-only, character-only, and combined features.

Run the security regression tests with:

```bash
python -m unittest discover -s tests -v
```

These tests verify the deterministic policy boundary, explicit lexical
fallback behavior, model thresholding, and fail-closed handling of inference
errors. The evaluation remains a prototype benchmark: a research claim should
add an untouched external test set, near-duplicate detection, repeated seeds,
confidence intervals, and adaptive multilingual attacks.

## Version Control Hygiene

- Keep `.venv` and `__pycache__` out of the repository.
- Commit only the source code, documentation, and dependency files.
- Use descriptive commit messages for future changes.
