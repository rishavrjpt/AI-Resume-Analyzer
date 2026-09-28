"""
Section classification models:
1. Rule-based baseline matcher using heading heuristics and regex patterns.
2. ML-based classifier using TF-IDF feature extraction and calibrated Logistic Regression.
"""

import os
import re
from typing import Dict, List, Tuple, Any, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score, confusion_matrix


# Canonical section classes
CANONICAL_SECTIONS = [
    "summary",
    "skills",
    "experience",
    "education",
    "projects",
    "certifications",
    "other"
]

# Rule-based regex patterns for heading identification
HEADING_PATTERNS = {
    "summary": re.compile(r"^(professional\s+)?(summary|profile|about\s+me|objective|career\s+objective|executive\s+summary|background)(\s+statement)?$", re.IGNORECASE),
    "skills": re.compile(r"^(technical\s+|core\s+|key\s+)?(skills|competencies|technologies|proficiencies|expertise|tech\s+stack|areas\s+of\s+expertise|skills\s*&\s*competencies)(\s*matrix)?$", re.IGNORECASE),
    "experience": re.compile(r"^(professional\s+|work\s+|employment\s+|relevant\s+)?(experience|history|background|work\s+history|practical\s+experience)$", re.IGNORECASE),
    "education": re.compile(r"^(education|academic\s+background|degrees|academic\s+history|relevant\s+coursework|education\s*&\s*degrees)$", re.IGNORECASE),
    "projects": re.compile(r"^(technical\s+|key\s+|featured\s+|selected\s+|notable\s+|lab\s+|academic\s+)?(projects|achievements\s*&\s*projects|open\s+source)$", re.IGNORECASE),
    "certifications": re.compile(r"^(certifications|licenses|credentials|certifications\s*&\s*credentials)$", re.IGNORECASE),
}


class RuleBasedSectionClassifier:
    """
    Transparent rule-based baseline for section classification.
    Uses regex pattern matching on heading lines, length heuristics, and casing rules.
    """

    def __init__(self):
        self.patterns = HEADING_PATTERNS

    def predict_line(self, line: str) -> Tuple[str, float]:
        """
        Classifies a single line as a section heading or 'other'.
        Returns (predicted_class, confidence_score).
        """
        clean = line.strip()
        if not clean or len(clean) > 80:
            return "other", 0.90

        # Strip common trailing punctuation like colons
        clean_heading = re.sub(r"[:\-_#=*]+$", "", clean).strip()

        for section, pattern in self.patterns.items():
            if pattern.search(clean_heading):
                return section, 0.95

        # Check for secondary keywords
        lower = clean_heading.lower()
        if any(w in lower for w in ["summary", "profile", "objective"]) and len(clean.split()) <= 4:
            return "summary", 0.75
        if any(w in lower for w in ["skills", "competencies", "technologies"]) and len(clean.split()) <= 4:
            return "skills", 0.75
        if any(w in lower for w in ["experience", "employment"]) and len(clean.split()) <= 4:
            return "experience", 0.75
        if any(w in lower for w in ["education", "degree", "university", "coursework"]) and len(clean.split()) <= 4:
            return "education", 0.75
        if any(w in lower for w in ["projects", "portfolio"]) and len(clean.split()) <= 4:
            return "projects", 0.75
        if any(w in lower for w in ["certifications", "licenses"]) and len(clean.split()) <= 4:
            return "certifications", 0.75

        return "other", 0.60

    def predict(self, texts: List[str]) -> List[str]:
        return [self.predict_line(t)[0] for t in texts]


class MLSectionClassifier:
    """
    Machine Learning Section Classifier using word + character n-gram TF-IDF
    and class-weighted multinomial Logistic Regression.
    """

    def __init__(self, c_param: float = 1.5, max_features: int = 4000):
        self.c_param = c_param
        self.max_features = max_features
        self.pipeline: Optional[Pipeline] = None
        self.classes_: List[str] = CANONICAL_SECTIONS

    def fit(self, texts: List[str], labels: List[str]):
        """Trains the vectorizer and classifier pipeline."""
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 3),
                analyzer="word",
                max_features=self.max_features,
                lowercase=True,
                sublinear_tf=True
            )),
            ("clf", LogisticRegression(
                C=self.c_param,
                class_weight="balanced",
                max_iter=1000,
                random_state=42
            ))
        ])
        self.pipeline.fit(texts, labels)
        self.classes_ = list(self.pipeline.named_steps["clf"].classes_)
        return self

    def predict(self, texts: List[str]) -> List[str]:
        if self.pipeline is None:
            raise ValueError("Model is not trained yet.")
        return list(self.pipeline.predict(texts))

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        if self.pipeline is None:
            raise ValueError("Model is not trained yet.")
        return self.pipeline.predict_proba(texts)

    def predict_single(self, text: str) -> Tuple[str, float]:
        if self.pipeline is None:
            raise ValueError("Model is not trained yet.")
        probs = self.predict_proba([text])[0]
        max_idx = int(np.argmax(probs))
        return self.classes_[max_idx], float(probs[max_idx])

    def save(self, filepath: str):
        """Saves model pipeline to disk."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self.pipeline, filepath)

    @classmethod
    def load(cls, filepath: str) -> "MLSectionClassifier":
        """Loads trained pipeline from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        instance = cls()
        instance.pipeline = joblib.load(filepath)
        instance.classes_ = list(instance.pipeline.named_steps["clf"].classes_)
        return instance
