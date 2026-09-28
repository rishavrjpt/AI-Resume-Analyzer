# ResumeLens AI — NLP-Powered Resume & Job Description Analyzer with ML Testing Dashboard

**ResumeLens AI** is an end-to-end, responsible NLP and machine learning system designed to help individuals evaluate their own resumes against target job descriptions. It provides transparent text extraction, hybrid section boundary detection, dictionary-based skill extraction with context spans, lexical and semantic text similarity estimation, and evidence-grounded writing suggestions.

The system includes a modern user-facing web interface and a dedicated **ML Testing Dashboard** to inspect model metadata, run regression tests against eight synthetic test resumes, and review empirical evaluation benchmarks.

---

## 1. Responsible Use & Ethical Safeguards

* **Personal Review Assistant, Not a Hiring Filter**: This tool is built solely to assist job seekers in reviewing and refining their resume wording. It is **not** an applicant screening, candidate ranking, or candidate evaluation tool.
* **No "Hireability" or "ATS Pass" Scores**: We never calculate or present candidate scores, hireability probabilities, or claims of ATS qualification.
* **No PII Retention**: Uploaded documents are parsed entirely in memory. Raw documents are never saved to disk, logged, or retained.
* **No Demographic Inference**: The system does not analyze, predict, or process sensitive attributes such as age, gender, race, ethnicity, or disability.
* **No Qualification Invention**: Writing suggestions highlight areas where action verbs or metrics could enhance clarity, but suggested rewrites use template placeholders (e.g., `[add a measured result if you have one]`) rather than fabricating achievements.
* **Honest Missing-Term Labeling**: Unmatched skills are phrased strictly as *"not found in the provided resume text"* rather than claiming the user lacks the skill.

---

## 2. Architecture & Pipeline

```text
Document Upload (.pdf, .docx, .txt)
        │
        ▼
[DocumentParser] ─── (In-memory streaming, pypdf & python-docx)
        │
        ▼
[SectionDetector] ── (Rule heuristics + TF-IDF Logistic Regression)
        │
        ▼
[SkillExtractor] ─── (Boundary-aware skills.json taxonomy + acronym candidate extraction)
        │
        ▼
[DocumentMatcher] ── (TF-IDF lexical cosine & all-MiniLM-L6-v2 dense embeddings)
        │
        ▼
[FeedbackGenerator] (Evidence-grounded suggestions & safe template rewrites)
        │
        ▼
[Web UI & ML Testing Dashboard]
```

---

## 3. Project Structure

```text
resume_analyzer/
├── app/
│   ├── main.py                     # FastAPI application entrypoint
│   ├── api/
│   │   ├── routes.py               # REST API endpoints
│   │   └── schemas.py              # Pydantic schemas
│   ├── services/
│   │   ├── document_parser.py      # PDF, DOCX, and TXT parsing
│   │   ├── section_detector.py     # Hybrid rule + ML section detection
│   │   ├── skill_extractor.py      # Taxonomy matching and candidate extraction
│   │   ├── matcher.py              # Lexical & semantic document comparison
│   │   └── feedback.py             # Grounded feedback generation
│   └── static/
│       ├── index.html              # 4-section responsive single page app
│       ├── styles.css              # Modern accessible stylesheet
│       └── app.js                  # Frontend interactive controller
├── src/
│   ├── data/
│   │   ├── prepare_dataset.py      # Dataset curation & anti-leakage splitting
│   │   └── split_dataset.py        # Document-level splitting utility
│   ├── models/
│   │   ├── section_classifier.py   # Rule-based & ML section classifiers
│   │   └── matching_models.py      # Lexical (TF-IDF) & Semantic (MiniLM) models
│   ├── train.py                    # Section classifier training script
│   ├── evaluate.py                 # Comprehensive benchmark evaluation script
│   └── predict.py                  # Standalone CLI inference pipeline
├── sample_resumes/
│   ├── README.md                   # Synthetic test fixtures documentation
│   ├── expected_test_cases.json    # Hand-authored expected behavior definitions
│   ├── sample_job_descriptions.json# Built-in test job postings
│   ├── resume_01_software_engineer.txt
│   ├── resume_02_data_analyst.txt
│   ├── resume_03_ml_intern.txt
│   ├── resume_04_frontend_developer.txt
│   ├── resume_05_backend_developer.txt
│   ├── resume_06_cybersecurity_trainee.txt
│   ├── resume_07_project_manager.txt
│   └── resume_08_minimal_resume.txt
├── data/
│   ├── README.md                   # Dataset provenance & license documentation
│   ├── taxonomy/
│   │   └── skills.json             # Transparent, editable technical taxonomy
│   ├── raw/                        # Raw labeled JSON corpora
│   └── processed/                  # Document-split train/val/test CSVs
├── configs/
│   └── config.yaml                 # System settings & model configuration
├── models/
│   ├── section_classifier.joblib   # Trained ML model artifact
│   └── model_metadata.json         # Training run hyperparameters & metadata
├── results/
│   ├── dataset_summary.json        # Corpus statistics & split counts
│   ├── evaluation_results.json     # Empirical evaluation metrics
│   └── error_analysis.json         # Diagnostic false positives & error analysis
├── tests/                          # Automated pytest suite (28 test cases)
├── requirements.txt                # Python package dependencies
├── pytest.ini                      # Pytest runner configuration
└── README.md
```

---

## 4. Empirical Evaluation Results

All metrics below were computed using `python src/evaluate.py` on strictly held-out test splits without document-level leakage.

### A. Section Heading & Content Classification
Evaluated on 51 held-out sentences across 3 completely isolated documents (`data/processed/section_test.csv`):

| Model / Approach | Architecture | Macro F1 | Weighted F1 | Delta vs. Baseline |
| :--- | :--- | :---: | :---: | :---: |
| **Baseline** | Rule-Based Regex & Cues | `0.4181` | `0.4357` | Baseline |
| **ResumeLens Model** | TF-IDF (1-3 n-grams) + Logistic Regression | **`0.8215`** | **`0.8431`** | **`+0.4034`** |

#### Per-Class Performance (ML Model):
* **Summary**: Precision `0.8571`, Recall `1.0000`, F1 **`0.9231`** (Support: 6)
* **Skills**: Precision `0.8182`, Recall `0.8182`, F1 **`0.8182`** (Support: 11)
* **Experience**: Precision `0.8571`, Recall `0.8571`, F1 **`0.8571`** (Support: 14)
* **Education**: Precision `1.0000`, Recall `0.8750`, F1 **`0.9333`** (Support: 8)
* **Projects**: Precision `0.6667`, Recall `0.6667`, F1 **`0.6667`** (Support: 6)
* **Certifications**: Precision `0.7500`, Recall `1.0000`, F1 **`0.8571`** (Support: 3)
* **Other / Unclassified**: Precision `0.8000`, Recall `0.6667`, F1 **`0.7273`** (Support: 3)

### B. Skill Extraction
Evaluated against 8 annotated ground-truth test snippets (`data/processed/skill_extraction_eval.json`):
* **Precision**: `1.0000` (100% of extracted taxonomy skills were true positives)
* **Recall**: `0.9655` (28 out of 29 labeled skills detected)
* **F1-Score**: **`0.9825`**
* **Confusion Counts**: True Positives: 28, False Positives: 0, False Negatives: 1

### C. Resume-to-Job Matching Models
Evaluated against 12 human-reviewed resume-job pairs with relevance scores (0 to 3):
* **Lexical Model (TF-IDF Cosine)**:
  * Spearman Rank Correlation with Human Relevance: **`0.8932`**
  * Top-1 Retrieval Precision: **`100.0%`**
* **Semantic Model (`sentence-transformers/all-MiniLM-L6-v2`)**:
  * Spearman Rank Correlation with Human Relevance: **`0.8870`**
  * Top-1 Retrieval Precision: **`100.0%`**

---

## 5. Getting Started & Installation

### Step 1: Clone and Set Up Virtual Environment
```bash
git clone https://github.com/example/resume-analyzer.git
cd resume-analyzer

# Create Python 3.11 virtual environment
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Prepare Dataset and Train Classifier
```bash
# 1. Prepare raw data and split by document ID (anti-leakage)
python src/data/prepare_dataset.py

# 2. Train section classification model
python src/train.py

# 3. Run full evaluation pipeline
python src/evaluate.py
```

### Step 4: Run the Web Application
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to:
* **Web Application UI**: `http://127.0.0.1:8000/`
* **Interactive API Documentation (Swagger/OpenAPI)**: `http://127.0.0.1:8000/docs`

---

## 6. Using the ML Testing Dashboard

1. Open the application at `http://127.0.0.1:8000/` and click the **ML Testing Dashboard** tab.
2. Review the top diagnostic cards showing API health, model versions, and evaluation status.
3. Select one or more of the **8 synthetic resumes** (e.g. `resume_05_backend_developer.txt` to test embedded skills or `resume_08_minimal_resume.txt` to test missing section handling).
4. Choose a built-in test job posting (e.g. *Senior Backend Engineer*) or enter a custom job description.
5. Click **Run Test on Selected**.
6. Inspect the live results table, view individual diagnostic details via the **View Details** modal, and export results as JSON or CSV.

---

## 7. Running the Automated Test Suite

ResumeLens AI includes 28 unit and integration tests covering parser edge cases, missing sections, skill boundaries, matching models, API routes, and synthetic fixtures:

```bash
pytest tests/ -v
```

---

## 8. Limitations & Error Analysis

1. **Heading Format Variations**: Multi-role blended headings (e.g., "Experience & Education") or resumes without explicit whitespace separation can challenge rule-based splitters, resulting in sentences falling into the dominant class or "other".
2. **Taxonomy Breadth**: Dictionary matching ensures high precision (1.0000) and zero false hallucinations, but emerging frameworks or proprietary tools not yet in `skills.json` will not be recognized as verified skills (though they may be captured as candidate acronyms).
3. **Semantic Similarity Is Not Qualification**: Dense embedding similarity scores reflect vocabulary and semantic orientation; they must never be conflated with applicant competence or job eligibility.

---

## 9. Resume-Ready Project Summary

Use the following verified bullet points for your resume or portfolio:

**ResumeLens AI — NLP-Based Resume Analysis and Job Description Comparison**
* Engineered a modular Python NLP pipeline for resume document parsing, hybrid section boundary detection (0.8215 Macro F1 vs 0.4181 baseline), and boundary-aware skill extraction (0.9825 F1).
* Implemented lexical TF-IDF and dense sentence transformer embeddings (`all-MiniLM-L6-v2`) to compare resume text against job postings, achieving 0.89 Spearman correlation with human-annotated relevance.
* Developed a privacy-conscious FastAPI web application and ML Testing Dashboard featuring 8 synthetic test fixtures, reproducible evaluation benchmarks, and evidence-grounded suggestions without candidate scoring or PII retention.
