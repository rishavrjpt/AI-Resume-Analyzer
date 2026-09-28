"""
Unit tests for Section Detector and Section Classifier.
"""

import pytest
from app.services.section_detector import SectionDetector
from src.models.section_classifier import RuleBasedSectionClassifier, MLSectionClassifier


def test_rule_based_heading_patterns():
    clf = RuleBasedSectionClassifier()
    assert clf.predict_line("EXPERIENCE")[0] == "experience"
    assert clf.predict_line("PROFESSIONAL EXPERIENCE")[0] == "experience"
    assert clf.predict_line("TECHNICAL SKILLS")[0] == "skills"
    assert clf.predict_line("EDUCATION BACKGROUND")[0] == "education"
    assert clf.predict_line("CAREER OBJECTIVE")[0] == "summary"
    assert clf.predict_line("CERTIFICATIONS")[0] == "certifications"
    assert clf.predict_line("KEY PROJECTS")[0] == "projects"
    assert clf.predict_line("This is just a normal sentence with no heading.")[0] == "other"


def test_section_detector_segmentation():
    detector = SectionDetector()
    lines = [
        "Jane Doe | jane@example.local",
        "PROFESSIONAL SUMMARY",
        "Passionate full-stack developer with 3 years of experience in Python and React.",
        "SKILLS",
        "Python, React, PostgreSQL, Docker",
        "WORK EXPERIENCE",
        "Software Engineer at Acme Corp from 2021 to 2024.",
        "Designed REST APIs and reduced query latency.",
        "EDUCATION",
        "B.S. in Computer Science, University of California, 2021"
    ]
    res = detector.detect_sections(lines)
    detected = res["detected_sections"]
    sections = res["sections"]

    assert "summary" in detected
    assert "skills" in detected
    assert "experience" in detected
    assert "education" in detected
    assert "Passionate full-stack developer" in sections["summary"]
    assert "Python, React" in sections["skills"]
    assert "projects" in res["missing_sections"]


def test_section_detector_missing_handling():
    detector = SectionDetector()
    sparse_lines = [
        "Alex Worker",
        "SKILLS",
        "Python, SQL"
    ]
    res = detector.detect_sections(sparse_lines)
    assert "skills" in res["detected_sections"]
    assert "experience" in res["missing_sections"]
    assert "education" in res["missing_sections"]
    assert "summary" in res["missing_sections"]
