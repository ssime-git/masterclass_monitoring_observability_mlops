from __future__ import annotations

from time import perf_counter, sleep

from opentelemetry import trace

KEYWORDS = {
    "billing": ("invoice", "payment", "refund", "charge", "subscription"),
    "technical": ("error", "bug", "latency", "timeout", "crash"),
    "account": ("login", "password", "profile", "account", "session"),
}
tracer = trace.get_tracer(__name__)


def classify_document(text: str, delay_seconds: float = 0.0) -> tuple[str, float, float]:
    lower_text = text.lower()
    start_time = perf_counter()
    dynamic_delay = delay_seconds
    if len(text) > 180 or "latency" in lower_text:
        dynamic_delay += 0.35
    if dynamic_delay > 0:
        sleep(dynamic_delay)

    with tracer.start_as_current_span("model.keyword_scoring"):
        label_scores: dict[str, int] = dict.fromkeys(KEYWORDS, 0)
        for label, keywords in KEYWORDS.items():
            label_scores[label] = sum(keyword in lower_text for keyword in keywords)

    predicted_label = max(label_scores, key=lambda label: label_scores[label])
    highest_score = label_scores[predicted_label]
    confidence = 0.55 if highest_score == 0 else min(0.55 + 0.1 * highest_score, 0.95)
    processing_time_ms = (perf_counter() - start_time) * 1000
    return predicted_label, confidence, processing_time_ms
