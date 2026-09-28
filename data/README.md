# Dataset Documentation & Provenance

## Overview & Responsible Use

This dataset is created specifically for developing and evaluating ResumeLens AI's NLP components:
1. **Section Heading & Content Classification**: Distinguishing between resume sections (`summary`, `skills`, `experience`, `education`, `projects`, `certifications`, `other`).
2. **Skill Extraction Evaluation**: Evaluating precision, recall, and F1 of skill extraction against labeled spans.
3. **Resume-to-Job Matching Evaluation**: Evaluating ranking and similarity agreement on paired resumes and job descriptions.

## Privacy & Ethical Compliance

- **No Personal Identifiers (PII)**: All names, emails, phone numbers, and physical addresses are synthetic placeholders (e.g. `alex.chen@example.local`).
- **No Web Scraping**: In strict adherence to ethical guidelines, no resumes were scraped from job boards, LinkedIn, or personal portfolio websites.
- **License**: Creative Commons Zero (CC0 1.0 Universal) - Public Domain Dedication for synthetic experimental benchmarks.

## Data Splits & Anti-Leakage Guarantee

All section classification samples are grouped by `document_id`. The dataset preparation script splits data strictly at the document level (70% train, 15% validation, 15% test). Lines and paragraphs from the same source document never appear across multiple splits.

## Taxonomy & Classes

Section classes:
- `summary`: Professional summaries, career objectives, executive profiles.
- `skills`: Technical competencies, core skills, programming languages, tools.
- `experience`: Professional employment, work history, roles, responsibilities.
- `education`: Degrees, universities, graduation dates, academic honors, coursework.
- `projects`: Technical projects, open source repositories, lab projects.
- `certifications`: Industry certifications, credentials, licenses.
- `other`: Contact headers, publications, interests, unclassified text.
