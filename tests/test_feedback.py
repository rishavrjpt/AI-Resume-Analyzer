"""
Unit tests for FeedbackGenerator:
Verifies evidence grounding, non-fabrication of facts, and placeholder usage.
"""

import pytest
from app.services.feedback import FeedbackGenerator


def test_weak_verb_flagging():
    sections = {
        "experience": "Helped build internal data entry tools using Python.\nAssisted with database migrations."
    }
    feedback = FeedbackGenerator.generate_feedback(
        extracted_sections=sections,
        detected_sections=["experience"],
        missing_sections=["education", "projects"]
    )

    issues = [f["issue"] for f in feedback]
    assert any("passive helper phrasing" in issue.lower() for issue in issues)

    # Verify no fabricated statistics in rewrites
    for f in feedback:
        if f.get("example_rewrite"):
            rewrite = f["example_rewrite"]
            # Must contain placeholders or templates rather than invented hardcoded numbers
            assert "[" in rewrite and "]" in rewrite


def test_missing_sections_feedback():
    feedback = FeedbackGenerator.generate_feedback(
        extracted_sections={"experience": "Developed web applications."},
        detected_sections=["experience"],
        missing_sections=["education", "skills"]
    )
    categories = [f["category"] for f in feedback]
    assert "Structural Completeness" in categories
    target_sections = [f["target_section"] for f in feedback]
    assert "Education" in target_sections
    assert "Skills" in target_sections


def test_long_bullet_flagging():
    long_sentence = (
        "Designed and implemented an enterprise-grade cloud native distributed pipeline that handles multiple "
        "streams of asynchronous telemetry data coming from hundreds of edge devices across various regions while "
        "ensuring fault tolerance, minimal overhead, automated alerting, and disaster recovery replication mechanisms."
    )
    sections = {"experience": long_sentence}
    feedback = FeedbackGenerator.generate_feedback(
        extracted_sections=sections,
        detected_sections=["experience"],
        missing_sections=[]
    )
    categories = [f["category"] for f in feedback]
    assert "Readability & Conciseness" in categories
