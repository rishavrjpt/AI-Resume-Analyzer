# Synthetic Sample Resumes for ResumeLens AI

## Notice & Disclaimers

1. **Synthetic & Fictional**: All eight files in this directory (`resume_01` to `resume_08`) are completely synthetic, hand-authored test fixtures created solely for software testing and pipeline diagnostics. No personal data, real person's identity, contact information, or proprietary text is included.
2. **Functional Testing Only**: These files are designed to test parser robustness, section boundary detection, skill extraction edge cases, and missing section handling.
3. **Not Benchmark Ground Truth**: These files are not representative of real applicants and must not be used as an evaluation benchmark or to make claims about model performance or accuracy.
4. **Not Training Data**: These synthetic resumes are strictly test fixtures and are not part of any model training or validation split.

## Test Fixture Overview

* `resume_01_software_engineer.txt`: Standard format with explicit sections (Summary, Skills, Experience, Education, Projects).
* `resume_02_data_analyst.txt`: Reverse section order (Education first, followed by Skills, Experience, Projects).
* `resume_03_ml_intern.txt`: Academic and internship focus with Coursework, Projects, and Education before Experience.
* `resume_04_frontend_developer.txt`: Modern tech stack resume with descriptive project bullets and action-oriented experience.
* `resume_05_backend_developer.txt`: Embedded skills directly inside bullet points without a dedicated Skills section heading.
* `resume_06_cybersecurity_trainee.txt`: Certifications-heavy layout with lab projects and security tools.
* `resume_07_project_manager.txt`: Agile and cross-functional leadership focus, varied bullet punctuation and narrative bullets.
* `resume_08_minimal_resume.txt`: Sparse resume lacking Education, Projects, and Certifications to test missing-section handling.
