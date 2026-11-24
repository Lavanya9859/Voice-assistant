"""Train a CPU-friendly text classifier for malicious assistant intent detection.

Default data source:
    deepset/prompt-injections through the public Hugging Face Datasets Server.
    No account, API token, or commercial service is required.

The UCI SMS corpus remains available as an explicit legacy baseline, but is
not a valid substitute for an assistant-specific prompt-injection benchmark.

Example:
    python train_model.py
    python train_model.py --csv data/prompt_injection.csv --output models/security_model.pkl
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import random
import re
import urllib.request
import zipfile
from pathlib import Path
from typing import Iterable

import joblib
from secure_assistant import SecureInputValidator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

LOGGER = logging.getLogger(__name__)
HF_PROMPT_INJECTION_URL = (
    "https://datasets-server.huggingface.co/rows?"
    "dataset=deepset%2Fprompt-injections&config=default&split=train&offset=0&length=10000"
)
UCI_SMS_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
RANDOM_STATE = 42
ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")


def _normalize_label(label: object) -> str:
    """Map common public-dataset labels to the project taxonomy."""

    normalized = str(label).strip().lower()
    if normalized in {"1", "true", "malicious", "injection", "jailbreak", "attack", "spam"}:
        return "malicious"
    if normalized in {"0", "false", "benign", "safe", "normal", "ham"}:
        return "benign"
    raise ValueError(f"Unsupported label: {label!r}")


def download_prompt_injection_rows(url: str = HF_PROMPT_INJECTION_URL) -> list[tuple[str, str]]:
    """Download a no-key prompt-injection dataset from the HF rows API.

    The Datasets Server returns JSON in the form ``{"rows": [{"row": ...}]}``.
    The parser accepts the common ``text``/``label`` schema and also recognizes
    ``prompt``/``is_injection`` to make provenance-preserving extensions easy.
    """

    LOGGER.info("Downloading open prompt-injection data from %s", url)
    request = urllib.request.Request(url, headers={"User-Agent": "secure-assistant-research/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    rows: list[tuple[str, str]] = []
    for item in payload.get("rows", []):
        row = item.get("row", item)
        text = row.get("text", row.get("prompt", row.get("content", "")))
        label = row.get("label", row.get("is_injection", row.get("injection", None)))
        if text and label is not None:
            rows.append((str(text).strip(), _normalize_label(label)))
    if not rows:
        raise ValueError("Prompt-injection endpoint returned no usable text/label rows.")
    return rows


def download_uci_rows() -> list[tuple[str, str]]:
    """Download the public UCI corpus and return ``(text, label)`` rows."""

    LOGGER.info("Downloading the free UCI SMS Spam Collection.")
    with urllib.request.urlopen(UCI_SMS_URL, timeout=30) as response:
        archive_bytes = response.read()

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        data_name = next(name for name in archive.namelist() if name.endswith("SMSSpamCollection"))
        with archive.open(data_name) as data_file:
            rows = []
            for raw_line in io.TextIOWrapper(data_file, encoding="utf-8"):
                label, separator, text = raw_line.rstrip("\n").partition("\t")
                if separator and text:
                    rows.append((text, _normalize_label(label)))
    return rows


def load_csv_rows(csv_path: Path) -> list[tuple[str, str]]:
    """Load a CSV containing ``text`` and ``label`` columns.

    Accepted labels are benign/ham/safe and malicious/spam/injection/attack.
    Unknown labels fail loudly so accidental label corruption is not hidden.
    """

    label_map = {
        "benign": "benign",
        "ham": "benign",
        "safe": "benign",
        "malicious": "malicious",
        "spam": "malicious",
        "injection": "malicious",
        "attack": "malicious",
    }
    rows: list[tuple[str, str]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as data_file:
        reader = csv.DictReader(data_file)
        if not reader.fieldnames or not {"text", "label"}.issubset(reader.fieldnames):
            raise ValueError("CSV must contain 'text' and 'label' columns.")
        for row in reader:
            text = (row.get("text") or "").strip()
            raw_label = (row.get("label") or "").strip().lower()
            label = label_map.get(raw_label)
            if text and label:
                rows.append((text, label))
    return rows


def build_pipeline(feature_mode: str = "combined") -> Pipeline:
    """Build complementary word and character TF-IDF features.

    Word n-grams capture semantic phrases; character n-grams retain signal
    across inserted spaces, punctuation, and other simple obfuscations.
    """

    word = (
        "word_tfidf",
        TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            lowercase=True,
            sublinear_tf=True,
            min_df=1,
            max_features=80_000,
        ),
    )
    character = (
        "char_tfidf",
        TfidfVectorizer(
            analyzer="char",
            ngram_range=(3, 5),
            lowercase=True,
            sublinear_tf=True,
            min_df=1,
            max_features=120_000,
        ),
    )
    if feature_mode == "word":
        features = word[1]
    elif feature_mode == "char":
        features = character[1]
    elif feature_mode == "combined":
        features = FeatureUnion([word, character])
    else:
        raise ValueError(f"Unknown feature mode: {feature_mode}")
    return Pipeline(
        [
            ("features", features),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1_000,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def calibrate_threshold(
    labels: list[str], probabilities: list[float], max_false_negative_rate: float
) -> float:
    """Choose the lowest-FPR threshold subject to an FN-rate upper bound."""

    positive = [label == "malicious" for label in labels]
    candidates = sorted({0.0, 1.0, *probabilities}, reverse=True)
    feasible: list[tuple[float, float, float]] = []
    for threshold in candidates:
        predicted = [probability >= threshold for probability in probabilities]
        false_negatives = sum(actual and not guess for actual, guess in zip(positive, predicted))
        true_positives = sum(actual and guess for actual, guess in zip(positive, predicted))
        false_positives = sum(not actual and guess for actual, guess in zip(positive, predicted))
        negative_count = max(1, sum(not actual for actual in positive))
        positive_count = max(1, sum(positive))
        fn_rate = false_negatives / positive_count
        fp_rate = false_positives / negative_count
        precision = true_positives / max(1, true_positives + false_positives)
        if fn_rate <= max_false_negative_rate:
            feasible.append((fp_rate, -precision, threshold))
    if not feasible:
        raise ValueError("No threshold satisfies the requested false-negative bound.")
    return min(feasible)[2]


def deduplicate_rows(rows: Iterable[tuple[str, str]]) -> tuple[list[tuple[str, str]], int]:
    """Remove exact text duplicates while preserving conflicting labels."""

    unique: dict[str, tuple[str, str]] = {}
    conflicts: set[str] = set()
    total = 0
    for text, label in rows:
        total += 1
        key = re.sub(r"\s+", " ", text).strip().casefold()
        previous = unique.get(key)
        if previous is not None and previous[1] != label:
            conflicts.add(key)
        unique.setdefault(key, (text, label))
    for key in conflicts:
        unique.pop(key, None)
    return list(unique.values()), total - len(unique)


def calculate_metrics(
    labels: list[str], predictions: list[str], probabilities: list[float] | None = None
) -> dict[str, object]:
    """Return machine-readable classification metrics for reproducible reports."""

    precision, recall, f1, support = precision_recall_fscore_support(
        labels,
        predictions,
        labels=["benign", "malicious"],
        zero_division=0,
    )
    result: dict[str, object] = {
        "accuracy": round(float(accuracy_score(labels, predictions)), 6),
        "benign": {
            "precision": round(float(precision[0]), 6),
            "recall": round(float(recall[0]), 6),
            "f1": round(float(f1[0]), 6),
            "support": int(support[0]),
        },
        "malicious": {
            "precision": round(float(precision[1]), 6),
            "recall": round(float(recall[1]), 6),
            "f1": round(float(f1[1]), 6),
            "support": int(support[1]),
        },
        "macro_f1": round(float(f1.mean()), 6),
        "confusion_matrix": confusion_matrix(
            labels, predictions, labels=["benign", "malicious"]
        ).tolist(),
    }
    if probabilities is not None:
        actual = [label == "malicious" for label in labels]
        result["roc_auc"] = round(float(roc_auc_score(actual, probabilities)), 6)
        result["average_precision"] = round(
            float(average_precision_score(actual, probabilities)), 6
        )
    return result


def perturb_text(text: str, seed: int) -> str:
    """Apply deterministic, label-preserving text obfuscations for evaluation."""

    rng = random.Random(seed)
    leetspeak = str.maketrans({"a": "4", "e": "3", "i": "1", "o": "0", "s": "5"})
    transformed = "".join(character + (" " if rng.random() < 0.12 else "") for character in text)
    transformed = transformed.translate(leetspeak)
    insertion_point = min(len(transformed), rng.randrange(max(1, len(transformed) + 1)))
    return transformed[:insertion_point] + "\u200b" + transformed[insertion_point:]


def evaluate_perturbation(
    pipeline: Pipeline, texts: list[str], labels: list[str], threshold: float
) -> dict[str, object]:
    """Report degradation under whitespace, zero-width, and leetspeak changes."""

    perturbed = [perturb_text(text, RANDOM_STATE + index) for index, text in enumerate(texts)]
    probabilities = pipeline.predict_proba(perturbed)
    classes = list(pipeline.classes_)
    malicious_index = classes.index("malicious")
    scores = probabilities[:, malicious_index]
    predictions = ["malicious" if score >= threshold else "benign" for score in scores]
    print("\nAdversarial perturbation evaluation (label-preserving simulation):")
    print(classification_report(labels, predictions, labels=["benign", "malicious"], zero_division=0))
    return calculate_metrics(labels, predictions, scores.tolist())


def train(
    rows: Iterable[tuple[str, str]],
    output_path: Path,
    report_path: Path,
    test_size: float,
    max_false_negative_rate: float,
    dataset_source: str,
) -> None:
    """Train, calibrate, evaluate, and serialize a model bundle."""

    raw_dataset = list(rows)
    dataset, duplicate_count = deduplicate_rows(raw_dataset)
    texts = [text for text, _ in dataset]
    labels = [label for _, label in dataset]
    if len(set(labels)) != 2:
        raise ValueError("Training data must contain both benign and malicious labels.")
    if len(dataset) < 20:
        raise ValueError("At least 20 labeled examples are required for a useful split.")

    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts,
        labels,
        test_size=test_size,
        random_state=RANDOM_STATE,
        stratify=labels,
    )
    fit_texts, calibration_texts, fit_labels, calibration_labels = train_test_split(
        train_texts,
        train_labels,
        test_size=test_size,
        random_state=RANDOM_STATE,
        stratify=train_labels,
    )
    pipeline = build_pipeline("combined")
    pipeline.fit(fit_texts, fit_labels)
    classes = list(pipeline.classes_)
    malicious_index = classes.index("malicious")
    calibration_probabilities = pipeline.predict_proba(calibration_texts)[:, malicious_index]
    threshold = calibrate_threshold(
        calibration_labels,
        calibration_probabilities.tolist(),
        max_false_negative_rate,
    )
    test_probabilities = pipeline.predict_proba(test_texts)[:, malicious_index]
    predictions = ["malicious" if score >= threshold else "benign" for score in test_probabilities]

    print(f"Calibrated threshold: {threshold:.6f} (FN-rate bound: {max_false_negative_rate:.2%})")
    combined_metrics = calculate_metrics(test_labels, predictions, test_probabilities.tolist())
    print(classification_report(test_labels, predictions, labels=["benign", "malicious"], zero_division=0))
    print(f"ROC-AUC: {combined_metrics['roc_auc']:.4f}")
    print(f"Average precision: {combined_metrics['average_precision']:.4f}")
    perturbed_metrics = evaluate_perturbation(pipeline, test_texts, test_labels, threshold)
    validator = SecureInputValidator()
    lexical_predictions = [
        "benign" if validator.validate(text).is_allowed else "malicious"
        for text in test_texts
    ]

    ablations: dict[str, object] = {"combined": combined_metrics}
    for feature_mode in ("word", "char"):
        ablation_pipeline = build_pipeline(feature_mode)
        ablation_pipeline.fit(fit_texts, fit_labels)
        ablation_malicious_index = list(ablation_pipeline.classes_).index("malicious")
        calibration_scores = ablation_pipeline.predict_proba(calibration_texts)[:, ablation_malicious_index]
        ablation_threshold = calibrate_threshold(
            calibration_labels, calibration_scores.tolist(), max_false_negative_rate
        )
        scores = ablation_pipeline.predict_proba(test_texts)[:, ablation_malicious_index]
        ablation_predictions = [
            "malicious" if score >= ablation_threshold else "benign" for score in scores
        ]
        ablations[feature_mode] = {
            "threshold": round(float(ablation_threshold), 6),
            "metrics": calculate_metrics(test_labels, ablation_predictions, scores.tolist()),
        }
    report = {
        "random_state": RANDOM_STATE,
        "dataset_source": dataset_source,
        "raw_rows": len(raw_dataset),
        "deduplicated_rows": len(dataset),
        "removed_duplicate_or_conflicting_rows": duplicate_count,
        "test_size": test_size,
        "max_false_negative_rate": max_false_negative_rate,
        "split_sizes": {
            "fit": len(fit_texts),
            "calibration": len(calibration_texts),
            "test": len(test_texts),
        },
        "baselines": {
            "deterministic_validator": calculate_metrics(test_labels, lexical_predictions),
        },
        "ablations": ablations,
        "robustness": {
            "deterministic_perturbations": perturbed_metrics,
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    LOGGER.info("Saved evaluation report to %s", report_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "labels": ["benign", "malicious"],
            "random_state": RANDOM_STATE,
            "source_rows": len(dataset),
            "dataset_source": dataset_source,
            "threshold": threshold,
            "max_false_negative_rate": max_false_negative_rate,
            "feature_description": "word TF-IDF (1-2) + character TF-IDF (3-5)",
        },
        output_path,
    )
    LOGGER.info("Saved model bundle to %s", output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="Optional local CSV with text,label columns.")
    parser.add_argument("--url", default=HF_PROMPT_INJECTION_URL, help="No-key JSON dataset endpoint.")
    parser.add_argument("--uci-baseline", action="store_true", help="Use the UCI SMS proxy baseline explicitly.")
    parser.add_argument("--output", type=Path, default=Path("models/security_model.pkl"))
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/security_evaluation.json"),
        help="Path for the machine-readable evaluation and ablation report.",
    )
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--max-fnr", type=float, default=0.02, help="Maximum allowed malicious false-negative rate.")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    random.seed(RANDOM_STATE)
    args = parse_args()
    if not 0.0 <= args.max_fnr <= 1.0:
        raise ValueError("--max-fnr must be between 0 and 1")
    if args.csv:
        rows = load_csv_rows(args.csv)
        source = str(args.csv)
    elif args.uci_baseline:
        rows = download_uci_rows()
        source = UCI_SMS_URL
    else:
        rows = download_prompt_injection_rows(args.url)
        source = args.url
    LOGGER.info("Loaded %d labeled examples.", len(rows))
    train(rows, args.output, args.report, args.test_size, args.max_fnr, source)


if __name__ == "__main__":
    main()
