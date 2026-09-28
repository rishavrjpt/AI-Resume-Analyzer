"""
FastAPI routing endpoints for ResumeLens AI.
"""

import os
import json
import uuid
import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import JSONResponse

from app.api.schemas import (
    HealthResponse, ModelInfoResponse, AnalysisResponse,
    TestSamplesListResponse, RunSampleTestsRequest, RunSampleTestsResponse,
    SampleTestResultRow
)
from app.services.document_parser import DocumentParser, DocumentParseError
from app.services.section_detector import SectionDetector
from app.services.skill_extractor import SkillExtractor
from app.services.matcher import DocumentMatcher
from app.services.feedback import FeedbackGenerator
from src.predict import ResumeLensPipeline


router = APIRouter(prefix="/api", tags=["ResumeLens AI API"])

# Cache persistent pipeline instance
_pipeline: Optional[ResumeLensPipeline] = None

# In-memory storage for latest test run results
_latest_test_results: Optional[Dict[str, Any]] = None


def get_pipeline() -> ResumeLensPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ResumeLensPipeline()
    return _pipeline


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """
    Reports API operational status, model availability, dataset readiness,
    and synthetic testing fixtures count.
    """
    model_exists = os.path.exists("models/section_classifier.joblib")
    taxonomy_exists = os.path.exists("data/taxonomy/skills.json")
    dataset_exists = os.path.exists("data/processed/section_train.csv")
    eval_exists = os.path.exists("results/evaluation_results.json")

    sample_files = []
    if os.path.exists("sample_resumes"):
        sample_files = [f for f in os.listdir("sample_resumes") if f.endswith(".txt")]

    return HealthResponse(
        status="healthy",
        api_running=True,
        version="1.0.0",
        models_available={
            "section_classifier": model_exists,
            "skills_taxonomy": taxonomy_exists,
            "semantic_embeddings": True
        },
        dataset_prepared=dataset_exists,
        evaluation_completed=eval_exists,
        sample_resumes_count=len(sample_files)
    )


@router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """
    Returns metadata for section classification, skills taxonomy,
    and semantic embedding models along with dataset provenance.
    """
    meta_path = "models/model_metadata.json"
    eval_path = "results/evaluation_results.json"

    meta: Dict[str, Any] = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

    latest_eval_date = None
    eval_status = "Not run yet"
    if os.path.exists(eval_path):
        with open(eval_path, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
            eval_status = eval_data.get("status", "completed")
            latest_eval_date = eval_data.get("timestamp")

    return ModelInfoResponse(
        model_name=meta.get("model_name", "ResumeLens-Section-Classifier"),
        model_version=meta.get("model_version", "1.0.0"),
        model_type=meta.get("model_type", "TF-IDF (1-3 n-grams) + Class-Weighted Logistic Regression"),
        training_date=meta.get("training_date"),
        dataset_name=meta.get("dataset_name", "ResumeLens Curated Resume Section Corpus"),
        train_samples=meta.get("train_samples", 164),
        classes=meta.get("classes", ["summary", "skills", "experience", "education", "projects", "certifications", "other"]),
        semantic_model={
            "name": "sentence-transformers/all-MiniLM-L6-v2",
            "type": "Dense Sentence Transformer Embeddings",
            "license": "Apache-2.0",
            "role": "Semantic resume-to-job text similarity estimation",
            "offline_ready": True
        },
        evaluation_status=eval_status,
        latest_eval_date=latest_eval_date
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    resume_file: UploadFile = File(..., description="Resume document in PDF, DOCX, or TXT format"),
    job_description: Optional[str] = Form(None, description="Job description text for comparative analysis")
):
    """
    Uploads and analyzes a resume document:
    - Text extraction (in-memory, no persistent PII retention)
    - Section detection (Summary, Skills, Experience, Education, Projects, Certifications)
    - Skill and term extraction with context spans
    - Job description comparison (lexical and semantic text similarity estimates)
    - Evidence-grounded writing suggestions
    """
    pipeline = get_pipeline()

    try:
        file_bytes = await resume_file.read()
        filename = resume_file.filename or "uploaded_resume.txt"

        analysis = pipeline.analyze(
            resume_bytes=file_bytes,
            filename=filename,
            job_description=job_description
        )
        return analysis

    except DocumentParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/insights")
async def get_insights():
    """
    Returns actual saved model evaluation results, error analysis,
    and dataset summaries. Never returns fabricated data.
    """
    eval_path = "results/evaluation_results.json"
    dataset_path = "results/dataset_summary.json"
    error_path = "results/error_analysis.json"

    eval_data = None
    dataset_data = None
    error_data = None

    if os.path.exists(eval_path):
        with open(eval_path, "r", encoding="utf-8") as f:
            eval_data = json.load(f)

    if os.path.exists(dataset_path):
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset_data = json.load(f)

    if os.path.exists(error_path):
        with open(error_path, "r", encoding="utf-8") as f:
            error_data = json.load(f)

    return {
        "status": "success",
        "has_evaluation": eval_data is not None,
        "evaluation_summary": eval_data if eval_data else "Not run yet",
        "dataset_summary": dataset_data if dataset_data else "Not run yet",
        "error_analysis": error_data if error_data else "Not run yet"
    }


@router.get("/test-samples", response_model=TestSamplesListResponse)
async def list_test_samples():
    """
    Lists the 8 synthetic sample resumes, their test personas, edge cases,
    and built-in job descriptions for the ML Testing Dashboard.
    """
    cases_path = "sample_resumes/expected_test_cases.json"
    jobs_path = "sample_resumes/sample_job_descriptions.json"

    cases_data = []
    if os.path.exists(cases_path):
        with open(cases_path, "r", encoding="utf-8") as f:
            cases_data = json.load(f).get("cases", [])

    jobs_data = []
    if os.path.exists(jobs_path):
        with open(jobs_path, "r", encoding="utf-8") as f:
            jobs_data = json.load(f)

    return TestSamplesListResponse(
        total_samples=len(cases_data),
        samples=cases_data,
        built_in_job_descriptions=jobs_data
    )


@router.post("/test-samples/run", response_model=RunSampleTestsResponse)
async def run_sample_tests(request: RunSampleTestsRequest):
    """
    Runs live analysis on selected synthetic resumes against a chosen or custom job description.
    Updates the testing results table and stores run records.
    """
    global _latest_test_results
    pipeline = get_pipeline()

    # Determine job description text
    job_text = ""
    if request.custom_job_description and request.custom_job_description.strip():
        job_text = request.custom_job_description.strip()
    elif request.job_description_id:
        jobs_path = "sample_resumes/sample_job_descriptions.json"
        if os.path.exists(jobs_path):
            with open(jobs_path, "r", encoding="utf-8") as f:
                jobs = json.load(f)
                for j in jobs:
                    if j["id"] == request.job_description_id:
                        job_text = j["description"]
                        break

    results_rows: List[SampleTestResultRow] = []
    success_count = 0
    fail_count = 0

    for filename in request.selected_filenames:
        filepath = os.path.join("sample_resumes", filename)
        if not os.path.exists(filepath):
            results_rows.append(SampleTestResultRow(
                filename=filename,
                parsing_status="Failed (File Not Found)",
                line_count=0,
                word_count=0,
                sections_detected=[],
                sections_count=0,
                missing_sections=[],
                skills_extracted_count=0,
                extracted_skills_sample=[],
                matched_terms_count=0,
                not_found_terms_count=0,
                feedback_count=0,
                analysis_status="Error",
                error_message="Sample file does not exist in sample_resumes/."
            ))
            fail_count += 1
            continue

        try:
            with open(filepath, "rb") as f:
                file_bytes = f.read()

            analysis = pipeline.analyze(
                resume_bytes=file_bytes,
                filename=filename,
                job_description=job_text if job_text else None
            )

            sec_analysis = analysis["section_analysis"]
            skill_analysis = analysis["skill_analysis"]
            comp = analysis["job_comparison"]

            matched_count = 0
            not_found_count = 0
            lex_sim = None
            sem_sim = None

            if comp:
                matched_count = comp["term_comparison"]["total_matching"]
                not_found_count = comp["term_comparison"]["total_not_found"]
                lex_sim = comp["similarity_estimates"]["lexical_similarity_score"]
                sem_sim = comp["similarity_estimates"]["semantic_similarity_score"]

            skill_names = [s["name"] for s in skill_analysis["verified_skills"]]

            results_rows.append(SampleTestResultRow(
                filename=filename,
                parsing_status="Success",
                line_count=analysis["document_info"]["line_count"],
                word_count=analysis["document_info"]["word_count"],
                sections_detected=sec_analysis["detected_sections"],
                sections_count=len(sec_analysis["detected_sections"]),
                missing_sections=sec_analysis["missing_sections"],
                skills_extracted_count=len(skill_names),
                extracted_skills_sample=skill_names[:8],
                matched_terms_count=matched_count,
                not_found_terms_count=not_found_count,
                lexical_similarity=lex_sim,
                semantic_similarity=sem_sim,
                feedback_count=len(analysis["feedback_suggestions"]),
                analysis_status="Success",
                error_message=None,
                full_analysis=analysis
            ))
            success_count += 1

        except Exception as e:
            results_rows.append(SampleTestResultRow(
                filename=filename,
                parsing_status="Failed",
                line_count=0,
                word_count=0,
                sections_detected=[],
                sections_count=0,
                missing_sections=[],
                skills_extracted_count=0,
                extracted_skills_sample=[],
                matched_terms_count=0,
                not_found_terms_count=0,
                feedback_count=0,
                analysis_status="Failed",
                error_message=str(e)
            ))
            fail_count += 1

    run_response = RunSampleTestsResponse(
        run_id=f"run_{uuid.uuid4().hex[:8]}",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        total_tested=len(request.selected_filenames),
        successful_runs=success_count,
        failed_runs=fail_count,
        results=results_rows,
        disclaimer="Functional software testing results on synthetic fixtures. Do NOT use as benchmark claims or candidate evaluations."
    )

    _latest_test_results = run_response.model_dump()
    return run_response


@router.get("/test-samples/results")
async def get_latest_test_results():
    """
    Returns the latest synthetic test run results, or an empty state if not yet executed.
    """
    global _latest_test_results
    if _latest_test_results is None:
        return {"has_run": False, "message": "No test runs executed yet in this session."}
    return {"has_run": True, "data": _latest_test_results}
