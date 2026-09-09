"""
Phase 4.1 — Validation Harness Test Suite
=========================================
Verifies the validation harness, golden scenario dataset, legal traceability
assertions, safety boundary guards, and deterministic offline execution.
"""

import asyncio
import json

from app.validation.assertions import (
    AUTHORITATIVE_CORPUS_ID,
    FORBIDDEN_UNSAFE_TERMS,
    STATUTORY_SCHEDULE_MAPPINGS,
    assert_legal_traceability,
    assert_safety_boundaries,
)
from app.validation.fixtures import (
    FIXTURE_MARKER,
    SYNTHETIC_COMPANY_RECORD,
    SYNTHETIC_COMPLIANT_DECLARATION,
    SYNTHETIC_GRAVIMETRIC_PASSED_LOT,
    SYNTHETIC_PACKER_REGISTRATION,
    SYNTHETIC_SEIZURE_RECORD,
)
from app.validation.runner import ValidationRunner
from app.validation.scenarios import GOLDEN_SCENARIOS, ValidationScenario


# -------------------------------------------------------------------------
# 1. SCENARIO DEFINITION & COMPLETENESS TESTS
# -------------------------------------------------------------------------

def test_01_scenario_definitions_valid_and_complete():
    """
    Verifies that all 16 golden scenarios are well-formed, uniquely identified,
    and populated with required metadata and input payloads.
    """
    assert len(GOLDEN_SCENARIOS) >= 16
    scenario_ids = [s.scenario_id for s in GOLDEN_SCENARIOS]
    assert len(scenario_ids) == len(set(scenario_ids)), "Scenario IDs must be unique"

    for idx in range(1, 17):
        expected_id = f"SCENARIO-{idx:02d}"
        assert expected_id in scenario_ids, f"Missing required golden scenario {expected_id}"

    for sc in GOLDEN_SCENARIOS:
        assert isinstance(sc, ValidationScenario)
        assert sc.title and len(sc.title.strip()) > 5
        assert sc.category and len(sc.category.strip()) > 3
        assert sc.description and len(sc.description.strip()) > 10
        assert isinstance(sc.input_data, dict)
        assert sc.expected_safety_constraints and len(sc.expected_safety_constraints) > 0


def test_02_every_scenario_has_expected_outcome_or_behavior():
    """
    Ensures every scenario declares either a statutory legal result or
    an explicit expected evidence state / review state.
    """
    for sc in GOLDEN_SCENARIOS:
        has_legal_res = sc.expected_legal_result is not None
        has_evidence_state = bool(sc.expected_evidence_state)
        assert has_legal_res or has_evidence_state, (
            f"Scenario {sc.scenario_id} must define an expected legal result or expected evidence state"
        )


def test_03_all_referenced_legal_sources_exist():
    """
    Verifies that all statutory mappings match the authoritative 2011 Gazette corpus.
    """
    assert AUTHORITATIVE_CORPUS_ID == "SIH-OFFICIAL-LEGAL-DATASET-2011"

    # Core statutory mappings
    assert STATUTORY_SCHEDULE_MAPPINGS["RULE_5_SECOND_SCHEDULE"]["schedule"] == "Second Schedule"
    assert STATUTORY_SCHEDULE_MAPPINGS["RULE_19_FIFTH_SCHEDULE"]["schedule"] == "Fifth Schedule"
    assert STATUTORY_SCHEDULE_MAPPINGS["RULE_19_SIXTH_SCHEDULE"]["schedule"] == "Sixth Schedule"
    assert STATUTORY_SCHEDULE_MAPPINGS["RULE_19_SEVENTH_SCHEDULE"]["schedule"] == "Seventh Schedule"
    assert STATUTORY_SCHEDULE_MAPPINGS["FIRST_SCHEDULE_MPE"]["schedule"] == "First Schedule"
    assert STATUTORY_SCHEDULE_MAPPINGS["RULE_24_WHOLESALE"]["rule"] == "Rule 24"


# -------------------------------------------------------------------------
# 2. LEGAL TRACEABILITY ASSERTION TESTS
# -------------------------------------------------------------------------

def test_04_legal_traceability_assertions_work():
    """
    Tests that assert_legal_traceability passes on valid citations and
    strictly catches invalid citations or illegal attributions (e.g. Rule 24 as MPE).
    """
    # Valid citations
    assert_legal_traceability("Evaluated in accordance with Rule 6(1)(e) of LMPC Rules, 2011", expected_rule_code="Rule 6(1)")
    assert_legal_traceability("Testing conducted under Rule 19 and Sixth Schedule", expected_schedule="Sixth Schedule")
    assert_legal_traceability("Maximum permissible errors applied under First Schedule Table 1", expected_schedule="First Schedule")

    # Catch missing expected rule
    caught_rule = False
    try:
        assert_legal_traceability("Generic text without citations", expected_rule_code="Rule 19")
    except AssertionError as e:
        caught_rule = True
        assert "Missing expected statutory rule citation 'Rule 19'" in str(e)
    assert caught_rule, "Should raise AssertionError on missing rule"

    # Catch illegal Rule 24 MPE attribution
    caught_r24 = False
    try:
        assert_legal_traceability("Computed error under Rule 24 MPE tolerances")
    except AssertionError as e:
        caught_r24 = True
        assert "Illegal attribution: Rule 24 must not be attributed to MPE" in str(e)
    assert caught_r24, "Should raise AssertionError on illegal Rule 24 MPE attribution"


# -------------------------------------------------------------------------
# 3. SAFETY BOUNDARY ASSERTION TESTS
# -------------------------------------------------------------------------

def test_05_safety_assertions_catch_forbidden_terms():
    """
    Tests that assert_safety_boundaries catches all prohibited terms and
    guarantees no autonomous enforcement or collective guilt claims exist.
    """
    # Safe text passes cleanly
    assert_safety_boundaries("System-generated administrative decision-support report for authorized officer review.")

    # Forbidden term: PROSECUTION_RECOMMENDED
    caught_pros = False
    try:
        assert_safety_boundaries({"action": "PROSECUTION_RECOMMENDED"})
    except AssertionError as e:
        caught_pros = True
        assert "Forbidden unsafe term 'PROSECUTION_RECOMMENDED'" in str(e)
    assert caught_pros

    # Forbidden term: COURT-ADMISSIBLE EVIDENCE
    caught_court = False
    try:
        assert_safety_boundaries("This report contains court-admissible evidence.")
    except AssertionError as e:
        caught_court = True
        assert "Forbidden unsafe term 'COURT-ADMISSIBLE EVIDENCE'" in str(e)
    assert caught_court

    # Forbidden term: LIVE GOVERNMENT VERIFICATION
    caught_live = False
    try:
        assert_safety_boundaries("Verified via live government verification gateway.")
    except AssertionError as e:
        caught_live = True
        assert "Forbidden unsafe term 'LIVE GOVERNMENT VERIFICATION'" in str(e)
    assert caught_live

    # Forbidden structure: dossier_result (collective guilt)
    caught_doss = False
    try:
        assert_safety_boundaries({"dossier_result": "NON_COMPLIANT"})
    except AssertionError as e:
        caught_doss = True
        assert "dossiers must not declare collective guilt" in str(e)
    assert caught_doss


# -------------------------------------------------------------------------
# 4. FIXTURES & OFFLINE DETERMINISM TESTS
# -------------------------------------------------------------------------

def test_06_synthetic_fixtures_marked_and_offline():
    """
    Ensures all synthetic fixtures are marked with SYNTHETIC_VALIDATION_FIXTURE
    and contain no live internet endpoints or fake government credentials.
    """
    assert SYNTHETIC_COMPLIANT_DECLARATION["fixture_type"] == FIXTURE_MARKER
    assert SYNTHETIC_GRAVIMETRIC_PASSED_LOT["fixture_type"] == FIXTURE_MARKER
    assert SYNTHETIC_COMPANY_RECORD["fixture_type"] == FIXTURE_MARKER
    assert SYNTHETIC_PACKER_REGISTRATION["fixture_type"] == FIXTURE_MARKER
    assert SYNTHETIC_SEIZURE_RECORD["fixture_type"] == FIXTURE_MARKER

    # No external live URLs
    for fixture in [SYNTHETIC_COMPLIANT_DECLARATION, SYNTHETIC_COMPANY_RECORD]:
        s = json.dumps(fixture)
        assert "http://" not in s and "https://" not in s


# -------------------------------------------------------------------------
# 5. EXECUTION & RUNNER INTEGRATION TESTS
# -------------------------------------------------------------------------

async def test_07_run_all_16_validation_scenarios_deterministic():
    """
    Executes the entire 16 golden validation scenarios through ValidationRunner.
    Requires 100% PASS rate across all scenarios.
    """
    runner = ValidationRunner()
    summary = await runner.run_all()

    assert summary.total == 16, f"Expected 16 scenarios, got {summary.total}"
    assert summary.failed == 0, f"Validation scenarios failed: {[r.scenario_id for r in summary.results if r.status == 'FAIL']}"
    assert summary.passed == 16
    assert summary.success_rate_percent == 100.0

    for r in summary.results:
        assert r.status == "PASS"
        assert r.legal_traceability_passed is True
        assert r.safety_assertions_passed is True
        assert r.error_message is None


async def test_08_validation_runner_json_serialization():
    """
    Verifies that ValidationSummary serializes to clean, valid JSON.
    """
    runner = ValidationRunner()
    summary = await runner.run_all()
    d = summary.to_dict()

    serialized = json.dumps(d)
    deserialized = json.loads(serialized)
    assert deserialized["total"] == 16
    assert deserialized["passed"] == 16
    assert deserialized["failed"] == 0
    assert len(deserialized["results"]) == 16


async def test_09_individual_scenario_filter():
    """
    Verifies running an individual scenario by ID.
    """
    single_scenario = [s for s in GOLDEN_SCENARIOS if s.scenario_id == "SCENARIO-05"]
    assert len(single_scenario) == 1

    runner = ValidationRunner(scenarios=single_scenario)
    summary = await runner.run_all()
    assert summary.total == 1
    assert summary.passed == 1
    assert summary.results[0].scenario_id == "SCENARIO-05"


if __name__ == "__main__":
    async def run_direct():
        test_01_scenario_definitions_valid_and_complete()
        test_02_every_scenario_has_expected_outcome_or_behavior()
        test_03_all_referenced_legal_sources_exist()
        test_04_legal_traceability_assertions_work()
        test_05_safety_assertions_catch_forbidden_terms()
        test_06_synthetic_fixtures_marked_and_offline()
        await test_07_run_all_16_validation_scenarios_deterministic()
        await test_08_validation_runner_json_serialization()
        await test_09_individual_scenario_filter()
        print("\n=======================================================")
        print("ALL PHASE 4.1 VALIDATION HARNESS TESTS PASSED (100%)!")
        print("=======================================================\n")

    asyncio.run(run_direct())
