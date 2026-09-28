"""
Inference prediction script for ResumeLens AI.
Processes a resume document and optional job description text,
returning structured analysis including sections, skills, matching, and feedback.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.document_parser import DocumentParser
from app.services.section_detector import SectionDetector
from app.services.skill_extractor import SkillExtractor
from app.services.matcher import DocumentMatcher
from app.services.feedback import FeedbackGenerator


class ResumeLensPipeline:
    """
    End-to-end inference pipeline for ResumeLens AI.
    """

    def __init__(
        self,
        ml_model_path: str = "models/section_classifier.joblib",
        taxonomy_path: str = "data/taxonomy/skills.json"
    ):
        self.section_detector = SectionDetector(ml_model_path=ml_model_path)
        self.skill_extractor = SkillExtractor(taxonomy_path=taxonomy_path)
        self.matcher = DocumentMatcher(skill_extractor=self.skill_extractor)

    def analyze(self, resume_bytes: bytes, filename: str, job_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes complete parsing, section detection, skill extraction, matching, and feedback generation.
        """
        # 1. Document Parsing
        parsed_doc = DocumentParser.parse_bytes(filename, resume_bytes)
        clean_text = parsed_doc["clean_text"]
        lines = parsed_doc["lines"]

        # 2. Section Detection
        section_results = self.section_detector.detect_sections(lines)
        extracted_sections = section_results["sections"]

        # 3. Skill & Term Extraction
        resume_skill_analysis = self.skill_extractor.analyze_skills(clean_text)

        # 4. Job Description Matching (if provided)
        comparison_results = None
        if job_description and job_description.strip():
            comparison_results = self.matcher.compare(clean_text, job_description.strip())

        # 5. Evidence-Grounded Feedback Generation
        feedback_suggestions = FeedbackGenerator.generate_feedback(
            extracted_sections=extracted_sections,
            detected_sections=section_results["detected_sections"],
            missing_sections=section_results["missing_sections"],
            comparison_results=comparison_results
        )

        return {
            "document_info": {
                "filename": filename,
                "file_type": parsed_doc["file_type"],
                "byte_size": parsed_doc["byte_size"],
                "line_count": parsed_doc["line_count"],
                "word_count": parsed_doc["word_count"]
            },
            "clean_text_preview": clean_text[:800] + ("..." if len(clean_text) > 800 else ""),
            "section_analysis": section_results,
            "skill_analysis": resume_skill_analysis,
            "job_comparison": comparison_results,
            "feedback_suggestions": feedback_suggestions,
            "responsible_use_notice": (
                "ResumeLens AI provides descriptive text and skill comparisons to assist in personal resume review. "
                "It does not evaluate hireability, rank candidates, or predict applicant tracking system (ATS) decisions."
            )
        }


def main():
    parser = argparse.ArgumentParser(description="ResumeLens AI — Resume & Job Description Analyzer")
    parser.add_argument("--resume", type=str, required=True, help="Path to resume file (.pdf, .docx, or .txt)")
    parser.add_argument("--job", type=str, default="", help="Path to job description text file or text string")
    parser.add_argument("--output", type=str, default="", help="Path to save JSON output")

    args = parser.parse_args()

    if not os.path.exists(args.resume):
        print(f"Error: Resume file '{args.resume}' does not exist.")
        sys.exit(1)

    with open(args.resume, "rb") as f:
        resume_bytes = f.read()

    job_text = ""
    if args.job:
        if os.path.exists(args.job):
            with open(args.job, "r", encoding="utf-8") as f:
                job_text = f.read()
        else:
            job_text = args.job

    pipeline = ResumeLensPipeline()
    filename = os.path.basename(args.resume)
    results = pipeline.analyze(resume_bytes, filename, job_description=job_text)

    output_str = json.dumps(results, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_str)
        print(f"Analysis saved to {args.output}")
    else:
        print(output_str)


if __name__ == "__main__":
    main()
