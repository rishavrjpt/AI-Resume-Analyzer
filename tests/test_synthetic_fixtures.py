"""
Integration tests for the 8 synthetic resume test fixtures
against sample_resumes/expected_test_cases.json.
"""

import os
import json
import pytest
from src.predict import ResumeLensPipeline


def test_all_eight_synthetic_resumes_against_expected_cases():
    cases_file = "sample_resumes/expected_test_cases.json"
    assert os.path.exists(cases_file), f"Expected test cases file not found at {cases_file}"

    with open(cases_file, "r", encoding="utf-8") as f:
        cases_data = json.load(f)

    cases = cases_data["cases"]
    assert len(cases) == 8, f"Expected 8 cases, found {len(cases)}"

    pipeline = ResumeLensPipeline()

    for case in cases:
        filename = case["filename"]
        filepath = os.path.join("sample_resumes", filename)
        assert os.path.exists(filepath), f"Sample resume file not found: {filepath}"

        with open(filepath, "rb") as f:
            file_bytes = f.read()

        results = pipeline.analyze(file_bytes, filename)
        assert results is not None

        detected_sections = results["section_analysis"]["detected_sections"]
        missing_sections = results["section_analysis"]["missing_sections"]

        # 1. Verify expected missing sections
        for expected_missing in case.get("expected_missing_sections", []):
            assert expected_missing in missing_sections or expected_missing not in detected_sections, (
                f"In {filename}, expected section {expected_missing} to be missing."
            )

        # 2. Verify minimum required skills are extracted
        extracted_skills = {s["name"].lower() for s in results["skill_analysis"]["verified_skills"]}
        extracted_aliases = {s["matched_alias"].lower() for s in results["skill_analysis"]["verified_skills"]}
        all_skill_tokens = extracted_skills.union(extracted_aliases)
        alias_map = pipeline.skill_extractor.alias_to_skill

        for required_skill in case.get("minimum_required_skills", []):
            req = required_skill.lower()
            canonical_target = alias_map.get(req, {}).get("canonical_name", "").lower()
            matched = (
                req in all_skill_tokens or
                (canonical_target and canonical_target in extracted_skills) or
                any(req in s or s in req for s in all_skill_tokens)
            )
            assert matched, (
                f"In {filename}, expected skill '{required_skill}' was not extracted. "
                f"Found skills: {extracted_skills}"
            )
