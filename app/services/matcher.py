"""
Resume to Job Description Matcher service.
Computes lexical (TF-IDF) and semantic (Sentence Transformer) text similarity estimates,
and produces granular skill overlap and missing-term comparative analyses.
"""

from typing import Dict, List, Tuple, Any, Optional, Set
from src.models.matching_models import LexicalMatcher, SemanticMatcher
from app.services.skill_extractor import SkillExtractor


class DocumentMatcher:
    """
    Compares resume text with job description text.
    Provides lexical and semantic similarity estimates and skill set intersections.
    """

    def __init__(self, skill_extractor: Optional[SkillExtractor] = None):
        self.lexical_matcher = LexicalMatcher()
        self.semantic_matcher = SemanticMatcher()
        self.skill_extractor = skill_extractor or SkillExtractor()

    def compare(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """
        Runs comprehensive text and skill comparison between resume and job description.
        """
        # 1. Skill extraction for both documents
        resume_analysis = self.skill_extractor.analyze_skills(resume_text)
        job_analysis = self.skill_extractor.analyze_skills(job_description)

        resume_skills_map = {s["name"]: s for s in resume_analysis["verified_skills"]}
        job_skills_map = {s["name"]: s for s in job_analysis["verified_skills"]}

        resume_skill_set = set(resume_skills_map.keys())
        job_skill_set = set(job_skills_map.keys())

        # Intersections
        matching_skill_names = sorted(list(resume_skill_set.intersection(job_skill_set)))
        not_found_in_resume = sorted(list(job_skill_set.difference(resume_skill_set)))
        additional_resume_skills = sorted(list(resume_skill_set.difference(job_skill_set)))

        matching_terms = [job_skills_map[name] for name in matching_skill_names]
        not_found_terms = [job_skills_map[name] for name in not_found_in_resume]
        additional_terms = [resume_skills_map[name] for name in additional_resume_skills]

        # 2. Text similarity estimates
        lexical_similarity = self.lexical_matcher.compute_similarity(resume_text, job_description)

        semantic_similarity = None
        semantic_status = "Available"
        try:
            if self.semantic_matcher.is_available():
                semantic_similarity = self.semantic_matcher.compute_similarity(resume_text, job_description)
            else:
                semantic_status = "Not loaded (offline / download pending)"
        except Exception as e:
            semantic_status = f"Unavailable ({str(e)})"

        # 3. Salient n-gram overlap
        top_resume_terms = [t[0] for t in self.lexical_matcher.extract_salient_terms(resume_text, top_n=20)]
        top_job_terms = [t[0] for t in self.lexical_matcher.extract_salient_terms(job_description, top_n=20)]
        shared_ngrams = sorted(list(set(top_resume_terms).intersection(set(top_job_terms))))

        # 4. Evidence-based explanation
        total_jd_skills = len(job_skill_set)
        match_count = len(matching_skill_names)
        match_pct = round((match_count / total_jd_skills * 100), 1) if total_jd_skills > 0 else 0.0

        explanation = (
            f"The provided job description explicitly mentions {total_jd_skills} technical terms from our taxonomy. "
            f"Of these, {match_count} ({match_pct}%) were detected in your resume text. "
            f"There are {len(not_found_in_resume)} job-description terms that were not found in your provided resume text. "
            f"Note: This comparison indicates wording overlap and semantic alignment between the two documents; "
            f"it does not evaluate candidate eligibility or predict hiring or ATS decisions."
        )

        return {
            "similarity_estimates": {
                "lexical_similarity_score": round(lexical_similarity, 3),
                "lexical_method": "TF-IDF N-Gram Cosine Similarity",
                "semantic_similarity_score": round(semantic_similarity, 3) if semantic_similarity is not None else None,
                "semantic_method": "all-MiniLM-L6-v2 Dense Embeddings (Apache-2.0)",
                "semantic_status": semantic_status,
                "label": "Text Similarity Estimate",
                "disclaimer": "These similarity estimates measure document vocabulary and embedding alignment. They do NOT predict interview calls, ATS pass rates, or hiring outcomes."
            },
            "term_comparison": {
                "matching_skills": matching_terms,
                "total_matching": len(matching_terms),
                "not_found_in_resume": not_found_terms,
                "total_not_found": len(not_found_terms),
                "additional_resume_skills": additional_terms,
                "total_additional": len(additional_terms),
                "shared_salient_terms": shared_ngrams
            },
            "document_stats": {
                "resume_skills_count": len(resume_skill_set),
                "job_skills_count": total_jd_skills,
                "coverage_percentage": match_pct
            },
            "explanation": explanation
        }
