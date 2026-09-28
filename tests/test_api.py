"""
Integration tests for FastAPI endpoints:
Tests health, model-info, analyze, insights, test-samples, and privacy safeguards.
"""

import os
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["api_running"] is True
    assert data["status"] == "healthy"
    assert data["sample_resumes_count"] >= 8


def test_api_model_info():
    response = client.get("/api/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "classes" in data
    assert "semantic_model" in data


def test_api_analyze_txt_file():
    resume_content = (
        "ALEX CHEN\n"
        "alex.chen@example.local\n\n"
        "SUMMARY\n"
        "Software engineer with 4 years building distributed systems.\n\n"
        "SKILLS\n"
        "Python, FastAPI, PostgreSQL, Docker, AWS\n\n"
        "EXPERIENCE\n"
        "Software Engineer | Acme\n"
        "- Built REST APIs using FastAPI and PostgreSQL.\n\n"
        "EDUCATION\n"
        "B.S. in Computer Science"
    )
    files = {
        "resume_file": ("alex_chen.txt", resume_content.encode("utf-8"), "text/plain")
    }
    data = {
        "job_description": "Looking for a Python and FastAPI engineer with PostgreSQL experience."
    }

    response = client.post("/api/analyze", files=files, data=data)
    assert response.status_code == 200
    result = response.json()

    assert "document_info" in result
    assert result["document_info"]["filename"] == "alex_chen.txt"
    assert "section_analysis" in result
    assert "summary" in result["section_analysis"]["detected_sections"]
    assert "skill_analysis" in result
    assert result["job_comparison"] is not None

    # Check matching skills
    matching_names = [s["name"] for s in result["job_comparison"]["term_comparison"]["matching_skills"]]
    assert "Python" in matching_names
    assert "FastAPI" in matching_names

    # Privacy check: Verify no file was persisted to current working directory
    assert not os.path.exists("alex_chen.txt")


def test_api_analyze_missing_file_error():
    response = client.post("/api/analyze", data={"job_description": "Python job"})
    assert response.status_code == 422  # Unprocessable Entity (Missing file)


def test_api_insights():
    response = client.get("/api/insights")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["has_evaluation"] is True
    assert "section_classification" in data["evaluation_summary"]


def test_api_test_samples():
    response = client.get("/api/test-samples")
    assert response.status_code == 200
    data = response.json()
    assert data["total_samples"] == 8
    assert len(data["built_in_job_descriptions"]) >= 3


def test_api_run_sample_tests():
    payload = {
        "selected_filenames": ["resume_01_software_engineer.txt", "resume_08_minimal_resume.txt"],
        "job_description_id": "jd_backend_engineer"
    }
    response = client.post("/api/test-samples/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_tested"] == 2
    assert data["successful_runs"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["filename"] == "resume_01_software_engineer.txt"
    assert data["results"][0]["parsing_status"] == "Success"
