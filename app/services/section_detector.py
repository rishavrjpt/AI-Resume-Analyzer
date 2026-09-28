"""
Section detector service for ResumeLens AI.
Combines rule-based heading patterns with trained ML classification
to segment resumes into canonical sections (Summary, Skills, Experience, Education, Projects, Certifications, Other).
"""

import os
import re
from typing import Dict, List, Tuple, Any, Optional
from src.models.section_classifier import RuleBasedSectionClassifier, MLSectionClassifier, CANONICAL_SECTIONS


class SectionDetector:
    """
    Detects and segments resume text into canonical sections.
    """

    EXPECTED_STANDARD_SECTIONS = ["summary", "skills", "experience", "education", "projects"]

    def __init__(self, ml_model_path: str = "models/section_classifier.joblib"):
        self.rule_classifier = RuleBasedSectionClassifier()
        self.ml_model_path = ml_model_path
        self.ml_classifier: Optional[MLSectionClassifier] = None
        self._load_ml_model()

    def _load_ml_model(self):
        """Attempts to load trained ML section classifier if available on disk."""
        if os.path.exists(self.ml_model_path):
            try:
                self.ml_classifier = MLSectionClassifier.load(self.ml_model_path)
            except Exception as e:
                print(f"[Warning] Could not load ML section classifier from {self.ml_model_path}: {e}")
                self.ml_classifier = None
        else:
            self.ml_classifier = None

    def is_likely_heading(self, line: str) -> Tuple[bool, str, float, str]:
        """
        Evaluates whether a single line is a section heading.
        Returns: (is_heading, section_label, confidence, method)
        """
        line_clean = line.strip()
        if not line_clean or len(line_clean) > 75:
            return False, "other", 0.0, "none"

        # Check rule-based first
        rule_label, rule_conf = self.rule_classifier.predict_line(line_clean)
        if rule_label != "other" and rule_conf >= 0.70:
            return True, rule_label, rule_conf, "rule_based"

        # Check line visual cues: ALL CAPS or short title case without trailing period
        words = line_clean.split()
        is_all_caps = line_clean.isupper() and len(words) <= 5 and not line_clean.endswith(".")
        is_short_title = line_clean.istitle() and len(words) <= 4 and not line_clean.endswith(".")

        if (is_all_caps or is_short_title) and self.ml_classifier is not None:
            try:
                ml_label, ml_conf = self.ml_classifier.predict_single(line_clean)
                if ml_label != "other" and ml_conf >= 0.55:
                    return True, ml_label, ml_conf, "ml_classifier"
            except Exception:
                pass

        return False, "other", 0.0, "none"

    def detect_sections(self, lines: List[str]) -> Dict[str, Any]:
        """
        Segments a list of text lines into canonical resume sections.
        """
        sections: Dict[str, List[str]] = {s: [] for s in CANONICAL_SECTIONS}
        heading_records: List[Dict[str, Any]] = []

        current_section = "other"  # Unclassified header before first explicit section

        for line_idx, line in enumerate(lines):
            line_str = line.strip()
            if not line_str:
                continue

            is_heading, section_label, conf, method = self.is_likely_heading(line_str)

            if is_heading:
                current_section = section_label
                heading_records.append({
                    "line_index": line_idx,
                    "heading_text": line_str,
                    "section": section_label,
                    "confidence": round(conf, 3),
                    "method": method
                })
            else:
                sections[current_section].append(line_str)

        # Build clean string representation per section
        extracted_sections: Dict[str, str] = {}
        for s in CANONICAL_SECTIONS:
            content = "\n".join(sections[s]).strip()
            if content:
                extracted_sections[s] = content

        detected_set = set(extracted_sections.keys())
        # Remove 'other' from core detected list if it only contains contact header
        detected_core_sections = [s for s in CANONICAL_SECTIONS if s in detected_set and s != "other"]
        missing_sections = [s for s in self.EXPECTED_STANDARD_SECTIONS if s not in detected_set]

        return {
            "sections": extracted_sections,
            "detected_sections": detected_core_sections,
            "total_detected": len(detected_core_sections),
            "missing_sections": missing_sections,
            "heading_records": heading_records,
            "has_ml_classifier": self.ml_classifier is not None,
            "classification_method": "hybrid (rule_based + ml)" if self.ml_classifier is not None else "rule_based_baseline"
        }
