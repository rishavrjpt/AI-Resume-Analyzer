"""
Unit tests for SkillExtractor service:
Tests multi-word terms, boundary handling, aliases, candidate terms, and context extraction.
"""

import pytest
from app.services.skill_extractor import SkillExtractor


def test_taxonomy_loading():
    extractor = SkillExtractor()
    assert len(extractor.skills_data) > 0
    assert "python" in extractor.alias_to_skill
    assert "postgresql" in extractor.alias_to_skill


def test_multi_word_and_special_char_skills():
    extractor = SkillExtractor()
    text = "Developed microservices in C++, Go, and Next.js with RESTful APIs deployed on Google BigQuery and AWS."
    skills = extractor.extract_skills(text)
    skill_names = {s["name"] for s in skills}

    assert "C++" in skill_names
    assert "Go" in skill_names
    assert "Next.js" in skill_names
    assert "RESTful APIs" in skill_names
    assert "Google BigQuery" in skill_names
    assert "AWS" in skill_names


def test_skill_context_snippets():
    extractor = SkillExtractor()
    text = "Implemented high-throughput messaging queue using Apache Kafka for real-time order streams."
    skills = extractor.extract_skills(text)
    kafka_skill = next((s for s in skills if s["name"] == "Apache Kafka"), None)

    assert kafka_skill is not None
    assert kafka_skill["matched_alias"] == "apache kafka"
    assert "messaging queue using Apache Kafka for real-time" in kafka_skill["context_snippet"]


def test_candidate_acronym_extraction():
    extractor = SkillExtractor()
    text = "Monitored SIEM log pipelines, verified compliance with WCAG, and maintained SOP playbooks."
    analysis = extractor.analyze_skills(text)
    candidate_names = {c["name"] for c in analysis["candidate_terms"]}

    assert "SIEM" in candidate_names
    assert "WCAG" in candidate_names
    assert "SOP" in candidate_names
