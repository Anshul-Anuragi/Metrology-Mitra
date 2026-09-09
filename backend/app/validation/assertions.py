"""
Phase 4.1 — Legal Traceability & Safety Boundary Assertions
===========================================================
Reusable assertion functions validating statutory traceability against
the official historical 2011 Gazette corpus (SIH-OFFICIAL-LEGAL-DATASET-2011)
and strictly enforcing safety constraints against legal overclaims.
"""

import json
import re
from typing import Any, Dict, List, Optional, Sequence, Union

AUTHORITATIVE_CORPUS_ID = "SIH-OFFICIAL-LEGAL-DATASET-2011"

# Prohibited unsafe terms that must NEVER appear in system outputs,
# API responses, or generated PDF reports
FORBIDDEN_UNSAFE_TERMS = [
    "PROSECUTION_RECOMMENDED",
    "RECOMMEND_PROSECUTION",
    "AUTONOMOUS_ENFORCEMENT",
    "COURT-ADMISSIBLE EVIDENCE",
    "COURT ADMISSIBLE EVIDENCE",
    "GOVERNMENT CERTIFIED",
    "GOVERNMENT-CERTIFIED",
    "LIVE GOVERNMENT VERIFICATION",
    "OFFICIAL GOVERNMENT DECREE",
    "AUTONOMOUS PENALTY ISSUANCE",
    "COLLECTIVE GUILT",
]

# Prohibited regex patterns for fabricated or autonomous claims
FORBIDDEN_UNSAFE_PATTERNS = [
    r"\bprosecute\s+the\s+director\b",
    r"\bdirector\s+is\s+personally\s+guilty\b",
    r"\bautomatic\s+director\s+liability\b",
    r"\bdossier\s+verdict:\s*(compliant|non_compliant)\b",
    r"\bthis\s+document\s+is\s+an\s+official\s+government\s+order\b",
]

# Statutory rule-to-schedule mappings mandated by the 2011 Gazette corpus
STATUTORY_SCHEDULE_MAPPINGS = {
    "RULE_5_SECOND_SCHEDULE": {
        "rule": "Rule 5",
        "schedule": "Second Schedule",
        "description": "Commodities to be packed in specified standard quantities",
    },
    "RULE_19_FIFTH_SCHEDULE": {
        "rule": "Rule 19",
        "schedule": "Fifth Schedule",
        "description": "Manner of selection of samples of packages for inspection",
    },
    "RULE_19_SIXTH_SCHEDULE": {
        "rule": "Rule 19",
        "schedule": "Sixth Schedule",
        "description": "Determination of net quantity and physical scale testing methodology",
    },
    "RULE_19_SEVENTH_SCHEDULE": {
        "rule": "Rule 19",
        "schedule": "Seventh Schedule",
        "description": "Form of report / data-sheet for recording test results",
    },
    "FIRST_SCHEDULE_MPE": {
        "rule": "Rule 2(e) / Rule 19",
        "schedule": "First Schedule",
        "description": "Maximum Permissible Errors on net quantities declared by weight, measure or number",
    },
    "RULE_24_WHOLESALE": {
        "rule": "Rule 24",
        "chapter": "Chapter III",
        "description": "Declarations applicable to wholesale packages (distinct from retail & MPE)",
    },
}


def assert_legal_traceability(
    finding_or_report: Union[str, Dict[str, Any], Sequence[Any]],
    expected_rule_code: Optional[str] = None,
    expected_schedule: Optional[str] = None,
    context: str = "Validation",
) -> None:
    """
    Validates that a statutory finding, check reason, or generated report contains
    correct legal traceability to the official 2011 Gazette dataset.
    """
    text_corpus = ""
    if isinstance(finding_or_report, str):
        text_corpus = finding_or_report
    elif isinstance(finding_or_report, dict):
        text_corpus = json.dumps(finding_or_report)
    elif isinstance(finding_or_report, (list, tuple)):
        text_corpus = " ".join([json.dumps(x) if isinstance(x, dict) else str(x) for x in finding_or_report])

    # 1. Verify Rule Code or Citation if requested
    if expected_rule_code:
        assert (
            expected_rule_code.lower() in text_corpus.lower()
            or expected_rule_code.replace("LMPC-", "").lower() in text_corpus.lower()
        ), f"[{context}] Missing expected statutory rule citation '{expected_rule_code}' in output text."

    # 2. Verify Schedule if requested
    if expected_schedule:
        assert expected_schedule.lower() in text_corpus.lower(), (
            f"[{context}] Missing expected statutory schedule citation '{expected_schedule}' in output text."
        )

    # 3. Guard against misattributing Rule 24 as MPE or Net-Quantity rule
    if "rule 24" in text_corpus.lower():
        # Rule 24 must not be described as the MPE rule or gravimetric net quantity test
        assert "rule 24 mpe" not in text_corpus.lower(), (
            f"[{context}] Illegal attribution: Rule 24 must not be attributed to MPE (MPE is under First Schedule)."
        )
        assert "rule 24 gravimetric" not in text_corpus.lower(), (
            f"[{context}] Illegal attribution: Rule 24 must not be described as gravimetric net-quantity determination."
        )


def assert_safety_boundaries(
    payload_or_text: Union[str, bytes, Dict[str, Any], Sequence[Any]],
    context: str = "SafetyBoundaryCheck",
) -> None:
    """
    Recursively scans text, bytes, or serialized JSON payloads to guarantee
    the absence of prohibited unsafe terms, autonomous enforcement claims,
    automatic personal director liability, or collective guilt verdicts.
    """
    if isinstance(payload_or_text, bytes):
        raw_text = payload_or_text.decode("latin-1", errors="ignore")
    elif isinstance(payload_or_text, str):
        raw_text = payload_or_text
    elif isinstance(payload_or_text, (dict, list, tuple)):
        raw_text = json.dumps(payload_or_text)
    else:
        raw_text = str(payload_or_text)

    upper_text = raw_text.upper()

    # 1. Exact forbidden term checks
    for term in FORBIDDEN_UNSAFE_TERMS:
        assert term not in upper_text, (
            f"[{context}] SAFETY VIOLATION: Forbidden unsafe term '{term}' detected in system output."
        )

    # 2. Regex pattern checks
    for pat in FORBIDDEN_UNSAFE_PATTERNS:
        match = re.search(pat, raw_text, re.IGNORECASE)
        assert not match, (
            f"[{context}] SAFETY VIOLATION: Forbidden unsafe pattern '{pat}' matched: '{match.group(0)}'."
        )

    # 3. Collective guilt in dossier synthesis checks
    if "dossier_result" in raw_text:
        assert False, f"[{context}] SAFETY VIOLATION: Field 'dossier_result' detected (dossiers must not declare collective guilt)."

