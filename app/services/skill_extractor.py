"""
Skill extraction service for ResumeLens AI.
Identifies technical skills and candidate terms using a transparent taxonomy,
boundary-aware alias matching, context span extraction, and technical term extraction.
"""

import os
import re
import json
from typing import Dict, List, Tuple, Any, Optional, Set


class SkillExtractor:
    """
    Extracts technical skills and key terms with span grounding and context snippets.
    Uses the transparent taxonomy in data/taxonomy/skills.json.
    """

    def __init__(self, taxonomy_path: str = "data/taxonomy/skills.json"):
        self.taxonomy_path = taxonomy_path
        self.skills_data: List[Dict[str, Any]] = []
        self.alias_to_skill: Dict[str, Dict[str, Any]] = {}
        self.compiled_patterns: List[Tuple[re.Pattern, str, Dict[str, Any]]] = []
        self._load_taxonomy()

    def _load_taxonomy(self):
        """Loads and compiles regex patterns from the taxonomy file."""
        if not os.path.exists(self.taxonomy_path):
            raise FileNotFoundError(f"Skills taxonomy file not found at {self.taxonomy_path}")

        with open(self.taxonomy_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.skills_data = data.get("skills", [])
        self.alias_to_skill = {}
        alias_tuples = []

        for skill in self.skills_data:
            canonical_name = skill["name"]
            category = skill.get("category", "General")
            aliases = skill.get("aliases", [canonical_name.lower()])
            # Add canonical name as alias too
            all_aliases = set(aliases + [canonical_name.lower()])

            for alias in all_aliases:
                clean_alias = alias.strip().lower()
                if not clean_alias:
                    continue
                skill_meta = {
                    "canonical_name": canonical_name,
                    "category": category,
                    "alias": clean_alias
                }
                self.alias_to_skill[clean_alias] = skill_meta
                alias_tuples.append((clean_alias, skill_meta))

        # Sort aliases by descending length so multi-word terms match before sub-tokens
        alias_tuples.sort(key=lambda x: len(x[0]), reverse=True)

        self.compiled_patterns = []
        for alias, meta in alias_tuples:
            escaped = re.escape(alias)
            # Handle boundaries carefully for terms with symbols (+, #, ., /)
            if alias in {"c++", "c#", ".net", "ci/cd", "a/b testing", "vue.js", "next.js", "node.js"}:
                pattern_str = r"(?:(?<=\s)|(?<=^)|(?<=[(,/]))" + escaped + r"(?:(?=\s)|(?=$)|(?=[),/;:.]))"
            elif alias in {"r", "c", "go"}:
                # Single letter or very short ambiguous keywords require strict isolation
                pattern_str = r"\b" + escaped + r"\b"
            else:
                pattern_str = r"\b" + escaped + r"\b"

            try:
                compiled = re.compile(pattern_str, re.IGNORECASE)
                self.compiled_patterns.append((compiled, alias, meta))
            except re.error:
                continue

    def extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts verified skills from text using boundary-aware taxonomy matching.
        Returns a list of extracted skills with matched spans, category, and context snippet.
        """
        if not text or not text.strip():
            return []

        matched_skills: Dict[str, Dict[str, Any]] = {}
        occupied_spans: List[Tuple[int, int]] = []

        for pattern, alias, meta in self.compiled_patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                matched_text = match.group(0)

                # Disambiguate single-letter/short words:
                # e.g., 'Go' in 'Go to', 'R' in 'Section R'
                if alias == "go":
                    if matched_text not in ["Go", "Golang"] and "programming" not in text.lower():
                        # If lowercase 'go', ensure it looks like a skill context
                        sub_ctx = text[max(0, start - 20):min(len(text), end + 20)].lower()
                        if not any(k in sub_ctx for k in ["python", "java", "backend", "grpc", "microservices"]):
                            continue
                elif alias == "r":
                    # Require 'R programming' or adjacent data tools
                    sub_ctx = text[max(0, start - 25):min(len(text), end + 25)].lower()
                    if not any(k in sub_ctx for k in ["python", "sql", "statistics", "data", "r stats", "r language"]):
                        continue

                # Check overlap with longer, already-matched spans
                overlaps = False
                for occ_s, occ_e in occupied_spans:
                    if not (end <= occ_s or start >= occ_e):
                        overlaps = True
                        break
                if overlaps:
                    continue

                canonical = meta["canonical_name"]
                if canonical not in matched_skills:
                    occupied_spans.append((start, end))

                    # Extract context snippet (up to 50 chars before and after)
                    context_start = max(0, start - 45)
                    context_end = min(len(text), end + 45)
                    snippet = text[context_start:context_end].strip()
                    if context_start > 0:
                        snippet = "..." + snippet
                    if context_end < len(text):
                        snippet = snippet + "..."

                    matched_skills[canonical] = {
                        "name": canonical,
                        "category": meta["category"],
                        "matched_alias": alias,
                        "matched_text": matched_text,
                        "span": [start, end],
                        "context_snippet": snippet,
                        "source": "taxonomy_match",
                        "confidence": 0.95
                    }

        return sorted(list(matched_skills.values()), key=lambda x: x["name"].lower())

    def extract_candidate_terms(self, text: str, existing_skills: List[str], max_terms: int = 15) -> List[Dict[str, Any]]:
        """
        Extracts salient technical acronyms and capitalized compound terms
        that might be domain-specific skills not yet in the core taxonomy.
        """
        if not text or not text.strip():
            return []

        existing_lower = {s.lower() for s in existing_skills}
        candidates: Dict[str, Dict[str, Any]] = {}

        # 1. Technical acronyms: 2-5 uppercase letters (e.g., SIEM, SOC, CVE, SOP, WCAG, LTV, KPI, EKS, IAM, BLoC)
        acronym_pattern = re.compile(r"\b[A-Z]{2,6}\b")
        common_words = {"AND", "THE", "FOR", "WITH", "THAT", "THIS", "FROM", "WILL", "HAVE", "BEEN", "INTO", "GPA", "USA", "ALL"}

        for match in acronym_pattern.finditer(text):
            acronym = match.group(0)
            if acronym in common_words or acronym.lower() in existing_lower:
                continue

            start, end = match.span()
            if acronym not in candidates:
                context_start = max(0, start - 35)
                context_end = min(len(text), end + 35)
                snippet = text[context_start:context_end].strip()
                candidates[acronym] = {
                    "name": acronym,
                    "category": "Candidate Acronym / Term",
                    "matched_alias": acronym,
                    "matched_text": acronym,
                    "span": [start, end],
                    "context_snippet": snippet,
                    "source": "candidate_extraction",
                    "confidence": 0.70
                }

        # Return top N candidates
        results = list(candidates.values())[:max_terms]
        return sorted(results, key=lambda x: x["name"])

    def analyze_skills(self, text: str) -> Dict[str, Any]:
        """
        Full skill and technical term analysis of a document.
        """
        verified_skills = self.extract_skills(text)
        skill_names = [s["name"] for s in verified_skills]
        candidate_terms = self.extract_candidate_terms(text, skill_names)

        # Group by category
        by_category: Dict[str, List[str]] = {}
        for s in verified_skills:
            cat = s["category"]
            by_category.setdefault(cat, []).append(s["name"])

        return {
            "verified_skills": verified_skills,
            "total_skills": len(verified_skills),
            "candidate_terms": candidate_terms,
            "total_candidates": len(candidate_terms),
            "by_category": by_category,
            "disclaimer": "Extracted terms reflect mentions found in the provided text and do not evaluate candidate proficiency or verify claimed qualifications."
        }
