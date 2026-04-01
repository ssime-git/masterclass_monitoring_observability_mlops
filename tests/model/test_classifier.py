from __future__ import annotations

from masterclass_mlops.model_logic import classify_document


def test_classifier_routes_billing_messages() -> None:
    label, confidence, processing_time_ms = classify_document(
        "I need a refund because the invoice was charged twice.",
    )

    assert label == "billing"
    assert confidence >= 0.65
    assert processing_time_ms >= 0


def test_classifier_routes_account_messages() -> None:
    label, _, _ = classify_document("My account login does not work after the password reset.")

    assert label == "account"
