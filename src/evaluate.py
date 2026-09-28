"""
Evaluation script for ResumeLens AI.
Evaluates:
1. Section Detection (Rule-Based baseline vs ML classifier) on held-out test split.
2. Skill Extraction against ground-truth annotated spans.
3. Resume-to-Job Matching (TF-IDF vs Semantic SentenceTransformers) on labeled pairs.
Saves reproducible metrics and error analysis under results/.
"""

import os
import sys
import json
import datetime

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Dict, List, Any
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score, confusion_matrix
from scipy.stats import spearmanr

from src.models.section_classifier import RuleBasedSectionClassifier, MLSectionClassifier, CANONICAL_SECTIONS
from app.services.skill_extractor import SkillExtractor
from app.services.matcher import DocumentMatcher


def evaluate_section_classification(test_csv_path: str, ml_model_path: str) -> Dict[str, Any]:
    """Evaluates rule-based and ML section classification on held-out test data."""
    if not os.path.exists(test_csv_path):
        raise FileNotFoundError(f"Test dataset not found at {test_csv_path}")

    test_df = pd.read_csv(test_csv_path)
    X_test = test_df["text"].astype(str).tolist()
    y_true = test_df["label"].astype(str).tolist()
    unique_labels = sorted(list(set(y_true)))

    # 1. Rule-based baseline evaluation
    rule_baseline = RuleBasedSectionClassifier()
    y_pred_rule = rule_baseline.predict(X_test)

    rule_macro_f1 = f1_score(y_true, y_pred_rule, average="macro", zero_division=0)
    rule_weighted_f1 = f1_score(y_true, y_pred_rule, average="weighted", zero_division=0)
    rule_report = classification_report(y_true, y_pred_rule, output_dict=True, zero_division=0)
    rule_cm = confusion_matrix(y_true, y_pred_rule, labels=unique_labels).tolist()

    # 2. ML Classifier evaluation
    if not os.path.exists(ml_model_path):
        raise FileNotFoundError(f"ML model not found at {ml_model_path}. Run train.py first.")

    ml_classifier = MLSectionClassifier.load(ml_model_path)
    y_pred_ml = ml_classifier.predict(X_test)

    ml_macro_f1 = f1_score(y_true, y_pred_ml, average="macro", zero_division=0)
    ml_weighted_f1 = f1_score(y_true, y_pred_ml, average="weighted", zero_division=0)
    ml_report = classification_report(y_true, y_pred_ml, output_dict=True, zero_division=0)
    ml_cm = confusion_matrix(y_true, y_pred_ml, labels=unique_labels).tolist()

    # Identify sample errors for error analysis
    errors = []
    for i, (text, true_lbl, pred_lbl) in enumerate(zip(X_test, y_true, y_pred_ml)):
        if true_lbl != pred_lbl:
            errors.append({
                "sample_index": i,
                "text": text,
                "true_label": true_lbl,
                "predicted_label": pred_lbl,
                "baseline_label": y_pred_rule[i]
            })

    return {
        "test_sample_count": len(test_df),
        "test_documents": int(test_df["document_id"].nunique()),
        "classes": unique_labels,
        "baseline_rule_based": {
            "macro_f1": round(float(rule_macro_f1), 4),
            "weighted_f1": round(float(rule_weighted_f1), 4),
            "per_class": {k: v for k, v in rule_report.items() if k in unique_labels},
            "confusion_matrix": rule_cm
        },
        "ml_classifier": {
            "macro_f1": round(float(ml_macro_f1), 4),
            "weighted_f1": round(float(ml_weighted_f1), 4),
            "per_class": {k: v for k, v in ml_report.items() if k in unique_labels},
            "confusion_matrix": ml_cm
        },
        "comparison_delta_macro_f1": round(float(ml_macro_f1 - rule_macro_f1), 4),
        "error_samples": errors[:8]
    }


def evaluate_skill_extraction(eval_json_path: str) -> Dict[str, Any]:
    """Evaluates SkillExtractor against ground-truth annotated skill spans."""
    if not os.path.exists(eval_json_path):
        raise FileNotFoundError(f"Skill eval dataset not found at {eval_json_path}")

    with open(eval_json_path, "r", encoding="utf-8") as f:
        eval_cases = json.load(f)

    extractor = SkillExtractor()
    total_tp = 0
    total_fp = 0
    total_fn = 0
    case_results = []
    sample_fps = []
    sample_fns = []

    for case in eval_cases:
        text = case["text"]
        gt_skills = set(case["ground_truth_skills"])
        analysis = extractor.analyze_skills(text)
        predicted = set(s["name"] for s in analysis["verified_skills"])

        tp = len(predicted.intersection(gt_skills))
        fp = len(predicted.difference(gt_skills))
        fn = len(gt_skills.difference(predicted))

        total_tp += tp
        total_fp += fp
        total_fn += fn

        for item in predicted.difference(gt_skills):
            sample_fps.append({"text": text, "false_positive": item})
        for item in gt_skills.difference(predicted):
            sample_fns.append({"text": text, "false_negative": item})

        case_results.append({
            "id": case["id"],
            "ground_truth": sorted(list(gt_skills)),
            "predicted": sorted(list(predicted)),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn
        })

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "evaluation_samples": len(eval_cases),
        "definition_of_correct_match": "Exact canonical taxonomy skill name match on annotated test sentences.",
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "total_true_positives": total_tp,
        "total_false_positives": total_fp,
        "total_false_negatives": total_fn,
        "sample_false_positives": sample_fps[:5],
        "sample_false_negatives": sample_fns[:5]
    }


def evaluate_matching_models(eval_json_path: str) -> Dict[str, Any]:
    """Evaluates lexical (TF-IDF) vs semantic (sentence embeddings) similarity against human relevance scores."""
    if not os.path.exists(eval_json_path):
        raise FileNotFoundError(f"Matching eval dataset not found at {eval_json_path}")

    with open(eval_json_path, "r", encoding="utf-8") as f:
        pairs = json.load(f)

    matcher = DocumentMatcher()

    relevance_scores = []
    lexical_scores = []
    semantic_scores = []
    has_semantic = matcher.semantic_matcher.is_available()

    for pair in pairs:
        rel = pair["relevance_score"]
        r_text = pair["resume_sample"]
        j_text = pair["job_sample"]

        comp = matcher.compare(r_text, j_text)
        lex_sim = comp["similarity_estimates"]["lexical_similarity_score"]
        relevance_scores.append(rel)
        lexical_scores.append(lex_sim)

        if has_semantic:
            sem_sim = comp["similarity_estimates"]["semantic_similarity_score"]
            semantic_scores.append(sem_sim if sem_sim is not None else 0.0)

    # Compute correlation with human relevance grades (0 to 3)
    lex_corr, _ = spearmanr(relevance_scores, lexical_scores)

    sem_corr = None
    if has_semantic and len(semantic_scores) == len(relevance_scores):
        sem_corr, _ = spearmanr(relevance_scores, semantic_scores)

    # Retrieval accuracy: Precision@1 on top-scoring document for relevant pairs
    # Group pairs by job_title to evaluate retrieval
    job_groups: Dict[str, List[Dict[str, Any]]] = {}
    for i, pair in enumerate(pairs):
        job = pair["job_title"]
        job_groups.setdefault(job, []).append({
            "is_relevant": pair["is_relevant"],
            "relevance_score": pair["relevance_score"],
            "lexical_score": lexical_scores[i],
            "semantic_score": semantic_scores[i] if has_semantic else 0.0
        })

    lex_p1_hits = 0
    sem_p1_hits = 0
    total_queries = len(job_groups)

    for job, items in job_groups.items():
        # Top-1 by lexical
        sorted_lex = sorted(items, key=lambda x: x["lexical_score"], reverse=True)
        if sorted_lex and sorted_lex[0]["is_relevant"] == 1:
            lex_p1_hits += 1

        # Top-1 by semantic
        if has_semantic:
            sorted_sem = sorted(items, key=lambda x: x["semantic_score"], reverse=True)
            if sorted_sem and sorted_sem[0]["is_relevant"] == 1:
                sem_p1_hits += 1

    lex_precision_at_1 = lex_p1_hits / total_queries if total_queries > 0 else 0.0
    sem_precision_at_1 = sem_p1_hits / total_queries if total_queries > 0 else None

    return {
        "evaluation_pairs_count": len(pairs),
        "evaluation_query_groups": total_queries,
        "evaluation_description": "Paired test samples with human-reviewed relevance scores (0-3). Evaluates retrieval ranking and score correlation.",
        "lexical_tfidf": {
            "model_description": "TF-IDF (1-2 n-grams) Cosine Similarity",
            "spearman_correlation_with_relevance": round(float(lex_corr), 4) if not np.isnan(lex_corr) else 0.0,
            "precision_at_1": round(float(lex_precision_at_1), 4)
        },
        "semantic_embeddings": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "license": "Apache-2.0",
            "is_available": has_semantic,
            "spearman_correlation_with_relevance": round(float(sem_corr), 4) if (sem_corr is not None and not np.isnan(sem_corr)) else None,
            "precision_at_1": round(float(sem_precision_at_1), 4) if sem_precision_at_1 is not None else None
        },
        "limitations_note": "Evaluated on a small, controlled 12-pair benchmark. These metrics reflect document similarity ranking, not hiring predictive validity."
    }


def run_evaluation():
    print("=" * 65)
    print("ResumeLens AI — Comprehensive NLP Pipeline Evaluation")
    print("=" * 65)

    test_csv = "data/processed/section_test.csv"
    ml_model = "models/section_classifier.joblib"
    skill_eval_json = "data/processed/skill_extraction_eval.json"
    matching_eval_json = "data/processed/matching_eval_pairs.json"
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)

    # 1. Section classification evaluation
    print("\n[1/3] Evaluating Section Classification (Baseline vs ML Classifier)...")
    section_results = evaluate_section_classification(test_csv, ml_model)
    print(f"Rule-Based Baseline Macro F1: {section_results['baseline_rule_based']['macro_f1']:.4f}")
    print(f"ML Classifier Macro F1:       {section_results['ml_classifier']['macro_f1']:.4f}")
    print(f"Delta (Improvement):          +{section_results['comparison_delta_macro_f1']:.4f}")

    # 2. Skill extraction evaluation
    print("\n[2/3] Evaluating Skill Extraction against Ground-Truth Spans...")
    skill_results = evaluate_skill_extraction(skill_eval_json)
    print(f"Skill Extraction Precision:   {skill_results['precision']:.4f}")
    print(f"Skill Extraction Recall:      {skill_results['recall']:.4f}")
    print(f"Skill Extraction F1-Score:    {skill_results['f1_score']:.4f}")

    # 3. Matching models evaluation
    print("\n[3/3] Evaluating Resume-to-Job Matching Models...")
    matching_results = evaluate_matching_models(matching_eval_json)
    print(f"Lexical (TF-IDF) Spearman Corr: {matching_results['lexical_tfidf']['spearman_correlation_with_relevance']}")
    print(f"Lexical (TF-IDF) Precision@1:  {matching_results['lexical_tfidf']['precision_at_1']}")
    if matching_results['semantic_embeddings']['is_available']:
        print(f"Semantic MiniLM Spearman Corr:  {matching_results['semantic_embeddings']['spearman_correlation_with_relevance']}")
        print(f"Semantic MiniLM Precision@1:   {matching_results['semantic_embeddings']['precision_at_1']}")

    # Assemble comprehensive evaluation output
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    evaluation_summary = {
        "evaluation_run_id": f"eval_run_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}",
        "timestamp": timestamp,
        "status": "completed",
        "section_classification": section_results,
        "skill_extraction": skill_results,
        "matching_models": matching_results
    }

    eval_out_path = os.path.join(results_dir, "evaluation_results.json")
    with open(eval_out_path, "w", encoding="utf-8") as f:
        json.dump(evaluation_summary, f, indent=2)

    error_analysis = {
        "timestamp": timestamp,
        "section_errors": section_results["error_samples"],
        "skill_false_positives": skill_results["sample_false_positives"],
        "skill_false_negatives": skill_results["sample_false_negatives"],
        "notes": (
            "Section classification errors typically occur on multi-role blended lines or vague headers. "
            "Skill extraction false negatives occur when abbreviations are not present in the taxonomy."
        )
    }
    error_out_path = os.path.join(results_dir, "error_analysis.json")
    with open(error_out_path, "w", encoding="utf-8") as f:
        json.dump(error_analysis, f, indent=2)

    print(f"\nSaved evaluation results to {eval_out_path}")
    print(f"Saved error analysis to {error_out_path}")
    print("=" * 65)
    return evaluation_summary


if __name__ == "__main__":
    run_evaluation()
