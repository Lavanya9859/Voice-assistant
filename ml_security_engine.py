"""Local ML security inference boundary for assistant commands."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from secure_assistant import SecureInputValidator

LOGGER = logging.getLogger("ml_security_engine")


@dataclass(frozen=True)
class SecurityDecision:
    """Auditable result returned for one untrusted input."""

    allowed: bool
    sanitized_text: str
    threat_probability: float
    latency_ms: float
    reason: str
    source: str
    evidence: tuple[str, ...] = ()


class MLSecurityEngine:
    """Run local model inference and apply a configurable fail-closed policy.

    The serialized bundle is expected to contain a scikit-learn pipeline under
    the ``pipeline`` key. If the artifact is not present, the engine remains
    operational using the deterministic validator, but labels the decision
    source as ``lexical_fallback`` so experiments cannot mistake fallback
    behavior for ML performance.
    """

    def __init__(
        self,
        model_path: str | Path = "models/security_model.pkl",
        threshold: float = 0.70,
        max_length: int = SecureInputValidator.DEFAULT_MAX_LENGTH,
    ) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0.0 and 1.0")
        self.model_path = Path(model_path)
        self.threshold = threshold
        self.validator = SecureInputValidator(max_length=max_length)
        self.pipeline: Any | None = None
        self.trained_threshold: float | None = None
        self._load_model()

    def _load_model(self) -> None:
        if not self.model_path.exists():
            LOGGER.warning("Model artifact not found at %s; using lexical fallback.", self.model_path)
            return
        try:
            import joblib

            bundle = joblib.load(self.model_path)
            self.pipeline = bundle["pipeline"]
            threshold = bundle.get("threshold")
            if threshold is not None:
                self.trained_threshold = float(threshold)
                self.threshold = self.trained_threshold
            LOGGER.info("Loaded local security model from %s", self.model_path)
        except (OSError, KeyError, TypeError, ValueError) as exc:
            LOGGER.error("Could not load model artifact: %s; using lexical fallback.", exc)

    def _explain_malicious_score(self, text: str, limit: int = 5) -> tuple[str, ...]:
        """Return highest positive linear feature contributions for this input."""

        if self.pipeline is None:
            return ()
        try:
            features = self.pipeline.named_steps["features"]
            classifier = self.pipeline.named_steps["classifier"]
            vector = features.transform([text])
            feature_names = features.get_feature_names_out()
            contributions = vector.multiply(classifier.coef_[0]).toarray()[0]
            ranked = sorted(
                ((float(score), name) for score, name in zip(contributions, feature_names) if score > 0),
                reverse=True,
            )
            return tuple(f"{name}={score:.4f}" for score, name in ranked[:limit])
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            LOGGER.exception("Could not compute model feature evidence.")
            return ()

    def inspect(self, text: str) -> SecurityDecision:
        """Inspect one command before it reaches assistant dispatch."""

        started = time.perf_counter()
        lexical_result = self.validator.validate(text)
        probability = 1.0 if not lexical_result.is_allowed else 0.0
        source = "lexical_fallback"
        reason = lexical_result.reason or "Input passed validation."
        evidence: tuple[str, ...] = (lexical_result.matched_rule,) if lexical_result.matched_rule else ()

        if lexical_result.is_allowed and self.pipeline is not None:
            try:
                probabilities = self.pipeline.predict_proba([lexical_result.sanitized_text])[0]
                classes = list(self.pipeline.classes_)
                malicious_index = classes.index("malicious")
                probability = float(probabilities[malicious_index])
                source = "local_tfidf_logistic_regression"
                reason = "Model probability is below the blocking threshold."
                evidence = self._explain_malicious_score(lexical_result.sanitized_text)
            except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
                LOGGER.exception("Model inference failed; blocking input: %s", exc)
                probability = 1.0
                source = "inference_failure_fail_closed"
                reason = "Model inference failed; input was blocked safely."

        allowed = lexical_result.is_allowed and probability < self.threshold
        if not allowed and lexical_result.is_allowed:
            reason = "Model probability reached the blocking threshold."
            evidence = self._explain_malicious_score(lexical_result.sanitized_text)
            LOGGER.warning("SECURITY_ALERT model_probability=%.4f threshold=%.4f", probability, self.threshold)

        latency_ms = (time.perf_counter() - started) * 1_000
        return SecurityDecision(
            allowed=allowed,
            sanitized_text=lexical_result.sanitized_text if allowed else "",
            threat_probability=max(0.0, min(1.0, probability)),
            latency_ms=latency_ms,
            reason=reason,
            source=source,
            evidence=evidence,
        )
