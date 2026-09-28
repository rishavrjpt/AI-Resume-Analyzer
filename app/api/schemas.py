"""
Pydantic schemas for ResumeLens AI API.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    api_running: bool = Field(True, description="API running flag")
    version: str = Field(..., description="Service version")
    models_available: Dict[str, bool] = Field(...)
    dataset_prepared: bool = Field(...)
    evaluation_completed: bool = Field(...)
    sample_resumes_count: int = Field(...)


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    model_type: str
    training_date: Optional[str] = None
    dataset_name: Optional[str] = None
    train_samples: Optional[int] = None
    classes: List[str]
    semantic_model: Dict[str, Any]
    evaluation_status: str
    latest_eval_date: Optional[str] = None


class SkillItem(BaseModel):
    name: str
    category: str
    matched_alias: str
    matched_text: str
    span: List[int]
    context_snippet: str
    source: str
    confidence: float


class SuggestionItem(BaseModel):
    id: str
    category: str
    severity: str
    target_section: str
    source_text: str
    issue: str
    explanation: str
    suggested_action: str
    example_rewrite: Optional[str] = None


class SimilarityEstimates(BaseModel):
    lexical_similarity_score: float
    lexical_method: str
    semantic_similarity_score: Optional[float] = None
    semantic_method: str
    semantic_status: str
    label: str
    disclaimer: str


class TermComparison(BaseModel):
    matching_skills: List[SkillItem]
    total_matching: int
    not_found_in_resume: List[SkillItem]
    total_not_found: int
    additional_resume_skills: List[SkillItem]
    total_additional: int
    shared_salient_terms: List[str]


class AnalysisResponse(BaseModel):
    document_info: Dict[str, Any]
    clean_text_preview: str
    section_analysis: Dict[str, Any]
    skill_analysis: Dict[str, Any]
    job_comparison: Optional[Dict[str, Any]] = None
    feedback_suggestions: List[SuggestionItem]
    responsible_use_notice: str


class SampleTestCase(BaseModel):
    filename: str
    persona: str
    edge_case_tested: str
    expected_sections: List[str]
    minimum_required_skills: List[str]
    expected_missing_sections: List[str]


class SampleTestJob(BaseModel):
    id: str
    title: str
    description: str


class TestSamplesListResponse(BaseModel):
    total_samples: int
    samples: List[SampleTestCase]
    built_in_job_descriptions: List[SampleTestJob]


class RunSampleTestsRequest(BaseModel):
    selected_filenames: List[str] = Field(..., description="List of sample resume filenames to run")
    job_description_id: Optional[str] = Field(None, description="Built-in job description ID")
    custom_job_description: Optional[str] = Field(None, description="Custom job description text entered by user")


class SampleTestResultRow(BaseModel):
    filename: str
    parsing_status: str
    line_count: int
    word_count: int
    sections_detected: List[str]
    sections_count: int
    missing_sections: List[str]
    skills_extracted_count: int
    extracted_skills_sample: List[str]
    matched_terms_count: int
    not_found_terms_count: int
    lexical_similarity: Optional[float] = None
    semantic_similarity: Optional[float] = None
    feedback_count: int
    analysis_status: str
    error_message: Optional[str] = None
    full_analysis: Optional[Dict[str, Any]] = None


class RunSampleTestsResponse(BaseModel):
    run_id: str
    timestamp: str
    total_tested: int
    successful_runs: int
    failed_runs: int
    results: List[SampleTestResultRow]
    disclaimer: str
