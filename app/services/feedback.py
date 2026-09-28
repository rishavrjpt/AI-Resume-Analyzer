"""
Evidence-grounded feedback generator for ResumeLens AI.
Analyzes extracted resume sections and sentences to produce concrete, actionable,
and honest suggestions tied strictly to user text, without fabricating achievements or metrics.
"""

import re
from typing import Dict, List, Tuple, Any, Optional


WEAK_ACTION_OPENERS = [
    (re.compile(r"^(helped\s+with|helped\s+build|helped\s+to|assisted\s+with|assisted\s+in)\b", re.IGNORECASE),
     "Begins with passive helper phrasing ('helped/assisted')",
     "Replace passive phrasing with a specific action verb describing what you personally built or executed (e.g., 'Implemented...', 'Engineered...', 'Maintained...')."),

    (re.compile(r"^(responsible\s+for|tasked\s+with|worked\s+on|involved\s+in)\b", re.IGNORECASE),
     "Uses passive duty description ('responsible for / worked on')",
     "State your direct contribution using an active verb (e.g., 'Architected...', 'Designed...', 'Authored...')."),

    (re.compile(r"^(handled|did|made)\b", re.IGNORECASE),
     "Uses a generic or non-descriptive verb",
     "Choose a more descriptive technical verb that specifies your methodology (e.g., 'Configured...', 'Streamlined...', 'Orchestrated...').")
]

MEASURABLE_OUTCOME_INDICATORS = re.compile(
    r"(\b\d+%\b|\b\d+x\b|\$\d+|\b\d+\s*(ms|s|hours|days|weeks|users|requests|endpoints|services|records|cves)\b)",
    re.IGNORECASE
)


class FeedbackGenerator:
    """
    Generates evidence-grounded resume feedback based on syntax, structure,
    and job description comparison.
    """

    @classmethod
    def generate_feedback(
        cls,
        extracted_sections: Dict[str, str],
        detected_sections: List[str],
        missing_sections: List[str],
        comparison_results: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Produces categorized, sentence-level feedback suggestions with safe template rewrites.
        """
        suggestions: List[Dict[str, Any]] = []
        s_id = 1

        # 1. Structural Suggestions: Missing standard sections
        for section in missing_sections:
            sec_display = section.capitalize()
            suggestions.append({
                "id": f"sug_{s_id}",
                "category": "Structural Completeness",
                "severity": "medium",
                "target_section": sec_display,
                "source_text": f"[Missing {sec_display} section]",
                "issue": f"No explicit '{sec_display}' section heading was identified in the document.",
                "explanation": (
                    f"Recruiters and hiring managers look for quick visual cues. If you have relevant {sec_display.lower()} "
                    f"experience or coursework, creating an explicit heading makes this information immediately discoverable."
                ),
                "suggested_action": f"Add an explicit '{sec_display.upper()}' heading followed by concise bullet points.",
                "example_rewrite": None
            })
            s_id += 1

        # 2. Sentence & Bullet Point Quality: Experience & Projects sections
        target_sections = [s for s in ["experience", "projects"] if s in extracted_sections]

        for sec_name in target_sections:
            content = extracted_sections[sec_name]
            lines = [line.strip() for line in content.splitlines() if line.strip()]

            for line in lines:
                # Clean leading bullet symbols (-, *, •, etc.)
                clean_bullet = re.sub(r"^[\s*•\-–—\d.)]+", "", line).strip()
                if len(clean_bullet) < 15:
                    continue

                words = clean_bullet.split()

                # Check 2a: Weak or passive opening verbs
                for pattern, issue_title, guidance in WEAK_ACTION_OPENERS:
                    if pattern.search(clean_bullet):
                        # Construct a non-inventing template rewrite
                        rewrite_prefix = re.sub(pattern, "[Strong Action Verb (e.g. Developed / Engineered)]", clean_bullet)
                        suggestions.append({
                            "id": f"sug_{s_id}",
                            "category": "Action Verb Clarity",
                            "severity": "medium",
                            "target_section": sec_name.capitalize(),
                            "source_text": line,
                            "issue": issue_title,
                            "explanation": (
                                "Stating what you specifically owned or achieved communicates clearer ownership than 'helped' or 'worked on'."
                            ),
                            "suggested_action": guidance,
                            "example_rewrite": f"{rewrite_prefix} [optional: resulting in a measurable outcome if you have one]"
                        })
                        s_id += 1
                        break  # Only one opener issue per line

                # Check 2b: Overly dense / long bullet points (> 35 words)
                if len(words) > 35:
                    suggestions.append({
                        "id": f"sug_{s_id}",
                        "category": "Readability & Conciseness",
                        "severity": "low",
                        "target_section": sec_name.capitalize(),
                        "source_text": line,
                        "issue": f"Bullet point is {len(words)} words long, which may be difficult to scan quickly.",
                        "explanation": (
                            "Dense sentences can cause critical technical details to be overlooked during a rapid initial review. "
                            "Consider splitting into two focused bullets or trimming non-essential filler words."
                        ),
                        "suggested_action": "Condense into 1-2 concise clauses focusing strictly on the technical problem and your specific solution.",
                        "example_rewrite": None
                    })
                    s_id += 1

                # Check 2c: Bullet lacking measurable context / impact indicator
                # Only flag for substantive project/experience bullets (>12 words) that don't already have numbers
                if len(words) >= 12 and not MEASURABLE_OUTCOME_INDICATORS.search(clean_bullet):
                    # Flag a few high-impact opportunities (limit to avoid overwhelming)
                    if s_id <= 10:
                        suggestions.append({
                            "id": f"sug_{s_id}",
                            "category": "Measurable Impact Opportunity",
                            "severity": "low",
                            "target_section": sec_name.capitalize(),
                            "source_text": line,
                            "issue": "Sentence describes technical responsibilities without a quantified outcome.",
                            "explanation": (
                                "Where feasible and factually accurate, adding measurable outcomes (e.g. latency reduced, "
                                "volume handled, tests added, users supported) provides tangible evidence of effectiveness."
                            ),
                            "suggested_action": "If you have recorded metrics for this project, append them to substantiate the result.",
                            "example_rewrite": f"{clean_bullet}, achieving [add a measured result if you have one, e.g., reducing latency or supporting N users]."
                        })
                        s_id += 1

        # 3. Job Description Alignment: Review prompts for not-found terms
        if comparison_results and "term_comparison" in comparison_results:
            not_found = comparison_results["term_comparison"].get("not_found_in_resume", [])
            for term_info in not_found[:5]:  # Top 5 review prompts
                skill_name = term_info["name"]
                cat = term_info.get("category", "Technical Skill")
                suggestions.append({
                    "id": f"sug_{s_id}",
                    "category": "Job Description Keyword Alignment",
                    "severity": "medium",
                    "target_section": "Skills & Experience",
                    "source_text": f"Job requirement: {skill_name} ({cat})",
                    "issue": f"'{skill_name}' is mentioned in the job description but was not found in your provided resume text.",
                    "explanation": (
                        f"If you have hands-on experience or project exposure with {skill_name}, consider referencing it in your "
                        f"skills section or within an applicable project description. If you do not have this experience, do not add it."
                    ),
                    "suggested_action": (
                        f"Review whether you have worked with {skill_name}. If yes, incorporate it into an existing experience bullet."
                    ),
                    "example_rewrite": f"Utilized {skill_name} to [describe your specific task or system component]."
                })
                s_id += 1

        return suggestions
