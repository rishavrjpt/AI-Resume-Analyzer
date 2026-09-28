"""
Unit tests for DocumentMatcher:
Covers TF-IDF lexical matching, semantic embeddings, bounds, and term set differences.
"""

import pytest
from app.services.matcher import DocumentMatcher


def test_lexical_similarity_bounds():
    matcher = DocumentMatcher()
    resume = "Experienced Python developer with FastAPI and PostgreSQL database skills."
    job = "Looking for a Python software engineer with PostgreSQL experience."
    comp = matcher.compare(resume, job)

    sim = comp["similarity_estimates"]["lexical_similarity_score"]
    assert 0.0 <= sim <= 1.0
    assert sim > 0.05  # Demonstrates positive lexical overlap


def test_empty_text_matching():
    matcher = DocumentMatcher()
    comp = matcher.compare("", "")
    assert comp["similarity_estimates"]["lexical_similarity_score"] == 0.0
    assert comp["term_comparison"]["total_matching"] == 0


def test_term_comparison_categorization():
    matcher = DocumentMatcher()
    resume = "Skills: Python, FastAPI, Docker."
    job = "Requirements: Python, Kubernetes, AWS."
    comp = matcher.compare(resume, job)
    tc = comp["term_comparison"]

    matching_names = {s["name"] for s in tc["matching_skills"]}
    not_found_names = {s["name"] for s in tc["not_found_in_resume"]}
    additional_names = {s["name"] for s in tc["additional_resume_skills"]}

    assert "Python" in matching_names
    assert "Kubernetes" in not_found_names or "AWS" in not_found_names
    assert "Docker" in additional_names


def test_similarity_disclaimer_presence():
    matcher = DocumentMatcher()
    comp = matcher.compare("Python developer", "Python developer")
    disclaimer = comp["similarity_estimates"]["disclaimer"]
    assert "NOT predict interview calls" in disclaimer
