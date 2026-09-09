"""
Phase 4.1 — Validation Package
===============================
Provides validation models, golden scenarios, assertions, and runner
for MetrologyMitra ministry-readiness evaluation.
"""

from app.validation.assertions import (
    AUTHORITATIVE_CORPUS_ID,
    FORBIDDEN_UNSAFE_TERMS,
    STATUTORY_SCHEDULE_MAPPINGS,
    assert_legal_traceability,
    assert_safety_boundaries,
)
from app.validation.fixtures import FIXTURE_MARKER
from app.validation.real_image_runner import (
    RealImageValidationItemResult,
    RealImageValidationRunner,
    RealImageValidationSummary,
    ReviewReasonCode,
)
from app.validation.runner import ScenarioResult, ValidationRunner, ValidationSummary
from app.validation.scenarios import GOLDEN_SCENARIOS, ValidationScenario

__all__ = [
    "ValidationScenario",
    "GOLDEN_SCENARIOS",
    "ValidationRunner",
    "ScenarioResult",
    "ValidationSummary",
    "RealImageValidationRunner",
    "RealImageValidationSummary",
    "RealImageValidationItemResult",
    "ReviewReasonCode",
    "assert_legal_traceability",
    "assert_safety_boundaries",
    "AUTHORITATIVE_CORPUS_ID",
    "FORBIDDEN_UNSAFE_TERMS",
    "STATUTORY_SCHEDULE_MAPPINGS",
    "FIXTURE_MARKER",
]

