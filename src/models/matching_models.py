"""
Matching models for comparing resume text with job descriptions:
1. LexicalMatcher: TF-IDF vectorization with cosine similarity.
2. SemanticMatcher: Pretrained sentence embeddings (all-MiniLM-L6-v2) with cosine similarity.
Both methods produce transparent similarity estimates and term comparisons without candidate ranking.
"""

import os
import re
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class LexicalMatcher:
    """
    Transparent lexical matching baseline using TF-IDF and cosine similarity.
    Calculates word and n-gram overlap between resume and job description.
    """

    def __init__(self, ngram_range: Tuple[int, int] = (1, 2), max_features: int = 5000):
        self.ngram_range = ngram_range
        self.max_features = max_features

    def compute_similarity(self, resume_text: str, job_text: str) -> float:
        """
        Computes cosine similarity between TF-IDF representations of resume and job description.
        Returns a float between 0.0 and 1.0.
        """
        if not resume_text.strip() or not job_text.strip():
            return 0.0

        vectorizer = TfidfVectorizer(
            ngram_range=self.ngram_range,
            max_features=self.max_features,
            stop_words="english",
            sublinear_tf=True
        )
        try:
            tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(np.clip(sim, 0.0, 1.0))
        except ValueError:
            return 0.0

    def extract_salient_terms(self, text: str, top_n: int = 25) -> List[Tuple[str, float]]:
        """Extracts top TF-IDF terms from a single document."""
        if not text.strip():
            return []
        vectorizer = TfidfVectorizer(
            ngram_range=self.ngram_range,
            max_features=self.max_features,
            stop_words="english"
        )
        try:
            matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = matrix.toarray()[0]
            top_indices = np.argsort(scores)[::-1][:top_n]
            return [(feature_names[i], float(scores[i])) for i in top_indices if scores[i] > 0]
        except ValueError:
            return []


class SemanticMatcher:
    """
    Semantic comparison using sentence embeddings (all-MiniLM-L6-v2).
    Model: sentence-transformers/all-MiniLM-L6-v2
    License: Apache-2.0
    Role: Computes dense semantic embedding similarity between document texts.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._is_available = False

    def is_available(self) -> bool:
        """Checks if the sentence-transformers library and model can be loaded."""
        if self._model is not None:
            return True
        try:
            import os
            # Prevent remote HEAD checks when running offline or in restricted sandbox
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            from sentence_transformers import SentenceTransformer
            try:
                self._model = SentenceTransformer(self.model_name, device=self.device, local_files_only=True)
            except TypeError:
                self._model = SentenceTransformer(self.model_name, device=self.device)
            self._is_available = True
            return True
        except Exception as e:
            # If offline load fails, fallback to disabled semantic mode
            self._is_available = False
            return False

    def compute_similarity(self, resume_text: str, job_text: str) -> float:
        """
        Computes cosine similarity between dense sentence embeddings.
        Returns float between 0.0 and 1.0.
        """
        if not resume_text.strip() or not job_text.strip():
            return 0.0

        if not self.is_available():
            raise RuntimeError(
                f"Semantic model '{self.model_name}' could not be loaded. Please ensure sentence-transformers is installed."
            )

        # Truncate texts appropriately to avoid out-of-context clipping
        resume_clean = resume_text.strip()[:4000]
        job_clean = job_text.strip()[:4000]

        embeddings = self._model.encode([resume_clean, job_clean], convert_to_numpy=True)
        sim = cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0]
        return float(np.clip(sim, 0.0, 1.0))
