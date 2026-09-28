"""
Dataset preparation script for ResumeLens AI.
Validates raw labeled data, normalizes text, masks PII,
splits into train/val/test by document ID to prevent data leakage,
and generates summary reports.
"""

import json
import os
import re
import random
from typing import Dict, List, Any
import pandas as pd


# Predefined labeled examples across 16 diverse synthetic documents
ANNOTATED_DOCUMENTS = [
    {
        "document_id": "doc_01",
        "domain": "software_engineering",
        "items": [
            {"text": "ALEX CHEN | alex.chen@example.local | San Francisco, CA", "label": "other"},
            {"text": "PROFESSIONAL SUMMARY", "label": "summary"},
            {"text": "Software Engineer with 4 years of experience building distributed backend systems, RESTful APIs, and cloud-native microservices.", "label": "summary"},
            {"text": "Passionate about system reliability, automated testing, and developer productivity.", "label": "summary"},
            {"text": "TECHNICAL SKILLS", "label": "skills"},
            {"text": "Programming Languages: Python, Go, Java, TypeScript", "label": "skills"},
            {"text": "Frameworks: FastAPI, Django, Flask, React, Docker, Kubernetes", "label": "skills"},
            {"text": "Databases & Cloud: PostgreSQL, Redis, MongoDB, AWS (EC2, S3, RDS)", "label": "skills"},
            {"text": "PROFESSIONAL EXPERIENCE", "label": "experience"},
            {"text": "Software Engineer | Acme Cloud Solutions | June 2022 - Present", "label": "experience"},
            {"text": "Designed and maintained high-throughput REST APIs using FastAPI and PostgreSQL, serving over 1.2M requests daily.", "label": "experience"},
            {"text": "Implemented asynchronous background task processing using Celery and Redis to handle batch data ingestion.", "label": "experience"},
            {"text": "Containerized legacy services with Docker and orchestrated deployments on AWS ECS using Terraform scripts.", "label": "experience"},
            {"text": "Led migration of relational schema to PostgreSQL 15, reducing average query latency by 32%.", "label": "experience"},
            {"text": "EDUCATION", "label": "education"},
            {"text": "Bachelor of Science in Computer Science", "label": "education"},
            {"text": "State University, Graduated May 2020 | GPA: 3.8/4.0", "label": "education"},
            {"text": "PROJECTS", "label": "projects"},
            {"text": "OpenAPI Mock Generator - Created an open-source CLI tool in Python that generates realistic synthetic JSON responses.", "label": "projects"},
            {"text": "Distributed Task Queue - Implemented a lightweight distributed message queue in Go using Raft consensus.", "label": "projects"}
        ]
    },
    {
        "document_id": "doc_02",
        "domain": "data_analytics",
        "items": [
            {"text": "JORDAN TAYLOR | Chicago, IL | jordan.taylor@example.local", "label": "other"},
            {"text": "EDUCATION", "label": "education"},
            {"text": "Master of Science in Business Analytics, Midwest Technical Institute, 2021", "label": "education"},
            {"text": "Bachelor of Science in Statistics, University of Illinois, 2019", "label": "education"},
            {"text": "SKILLS & COMPETENCIES", "label": "skills"},
            {"text": "Data Analysis & Modeling: SQL, Python (Pandas, NumPy, Scikit-Learn), R, Statistical Inference", "label": "skills"},
            {"text": "Visualization & BI: Tableau, Power BI, Matplotlib, Seaborn", "label": "skills"},
            {"text": "Data Warehousing: Snowflake, Google BigQuery, dbt, Apache Airflow", "label": "skills"},
            {"text": "WORK HISTORY", "label": "experience"},
            {"text": "Senior Data Analyst | Insightful Retail Analytics | July 2021 - Present", "label": "experience"},
            {"text": "Engineered automated reporting pipelines in dbt and BigQuery, eliminating 15 hours of manual weekly reporting.", "label": "experience"},
            {"text": "Designed and analyzed 24 A/B tests for checkout flow optimizations, generating 4.5% conversion uplift.", "label": "experience"},
            {"text": "Built interactive executive dashboards in Tableau tracking customer lifetime value (LTV) and churn metrics.", "label": "experience"},
            {"text": "KEY PROJECTS", "label": "projects"},
            {"text": "Customer Churn Prediction Engine - Developed a predictive classification pipeline using Scikit-Learn and Pandas.", "label": "projects"},
            {"text": "Retail Basket Market Analysis - Discovered cross-selling product associations from 500,000 retail transactions.", "label": "projects"}
        ]
    },
    {
        "document_id": "doc_03",
        "domain": "machine_learning",
        "items": [
            {"text": "SAMIRA KHAN | Seattle, WA | samira.khan@example.local", "label": "other"},
            {"text": "CAREER OBJECTIVE", "label": "summary"},
            {"text": "Motivated Computer Science graduate student seeking a Machine Learning Engineering Internship to apply deep learning and NLP.", "label": "summary"},
            {"text": "EDUCATION BACKGROUND", "label": "education"},
            {"text": "M.S. in Computer Science (Concentration: Artificial Intelligence), University of Washington, 2025", "label": "education"},
            {"text": "B.S. in Computer Engineering, Purdue University, 2023", "label": "education"},
            {"text": "RELEVANT COURSEWORK", "label": "education"},
            {"text": "Deep Learning, Natural Language Processing, Computer Vision, Distributed Systems, Reinforcement Learning", "label": "education"},
            {"text": "TECHNICAL EXPERTISE", "label": "skills"},
            {"text": "ML & Deep Learning: PyTorch, TensorFlow, Hugging Face Transformers, Scikit-Learn, SciPy", "label": "skills"},
            {"text": "Languages & Tools: Python, C++, SQL, Docker, Git, Linux, Weights & Biases", "label": "skills"},
            {"text": "RESEARCH & PROJECTS", "label": "projects"},
            {"text": "Clinical Note Entity Recognizer - Fine-tuned BERT-based transformer model using PyTorch to extract medical entities.", "label": "projects"},
            {"text": "Evaluated token classification performance using sequence labeling F1-score and confusion matrices.", "label": "projects"},
            {"text": "EXPERIENCE", "label": "experience"},
            {"text": "Graduate Research Assistant | UW NLP Lab | September 2023 - Present", "label": "experience"},
            {"text": "Conducted empirical research on parameter-efficient fine-tuning (LoRA) for large language models.", "label": "experience"},
            {"text": "Software Engineering Intern | DataWave Systems | June 2022 - August 2022", "label": "experience"}
        ]
    },
    {
        "document_id": "doc_04",
        "domain": "frontend_engineering",
        "items": [
            {"text": "LIAM O'CONNOR | Austin, TX | liam.oconnor@example.local", "label": "other"},
            {"text": "EXECUTIVE SUMMARY", "label": "summary"},
            {"text": "Frontend Engineer with 5+ years crafting accessible, responsive, and performant web applications in React and TypeScript.", "label": "summary"},
            {"text": "CORE SKILLS", "label": "skills"},
            {"text": "Web Technologies: JavaScript (ES6+), TypeScript, HTML5, CSS3, Tailwind CSS, Next.js", "label": "skills"},
            {"text": "Tooling & Testing: Webpack, Vite, Jest, Cypress, React Testing Library, ESLint", "label": "skills"},
            {"text": "EXPERIENCE", "label": "experience"},
            {"text": "Lead Frontend Developer | PixelCraft Media | Jan 2022 - Present", "label": "experience"},
            {"text": "Architected enterprise design system used across 8 production applications, reducing component duplication by 45%.", "label": "experience"},
            {"text": "Migrated legacy single-page application to Next.js 14, improving Core Web Vitals.", "label": "experience"},
            {"text": "Mentored 4 junior engineers on accessible web development (WCAG 2.1 AA compliance).", "label": "experience"},
            {"text": "EDUCATION", "label": "education"},
            {"text": "Bachelor of Fine Arts in Digital Media Design, University of Texas at Austin, 2018", "label": "education"},
            {"text": "FEATURED PROJECTS", "label": "projects"},
            {"text": "Accessible UI Component Library - Authored a fully headless, ARIA-compliant React component library.", "label": "projects"}
        ]
    },
    {
        "document_id": "doc_05",
        "domain": "backend_engineering",
        "items": [
            {"text": "MARCUS VANCE | Denver, CO | marcus.vance@example.local", "label": "other"},
            {"text": "PROFILE", "label": "summary"},
            {"text": "Backend Software Engineer focusing on microservice architectures, event-driven systems, and relational database optimization.", "label": "summary"},
            {"text": "WORK EXPERIENCE", "label": "experience"},
            {"text": "Senior Backend Engineer | Apex Logistics Platform | March 2021 - Present", "label": "experience"},
            {"text": "Built real-time package tracking microservices using Go, gRPC, and Apache Kafka handling 50,000 events/second.", "label": "experience"},
            {"text": "Designed database schemas in PostgreSQL and implemented caching layers using Redis clusters.", "label": "experience"},
            {"text": "Provisioned cloud infrastructure on GCP using Kubernetes and Terraform for automated deployments.", "label": "experience"},
            {"text": "TECHNICAL PROJECTS", "label": "projects"},
            {"text": "Event-Driven Order Processing Engine - Built fault-tolerant order pipeline using Python, FastAPI, and Pulsar.", "label": "projects"},
            {"text": "Distributed Rate Limiter - Implemented sliding-window counter rate limiting in Go backed by Redis Lua scripts.", "label": "projects"},
            {"text": "EDUCATION", "label": "education"},
            {"text": "Bachelor of Science in Information Systems, Colorado State University, 2018", "label": "education"}
        ]
    },
    {
        "document_id": "doc_06",
        "domain": "cybersecurity",
        "items": [
            {"text": "PRIYA PATEL | Dallas, TX | priya.patel@example.local", "label": "other"},
            {"text": "PROFESSIONAL SUMMARY", "label": "summary"},
            {"text": "Cybersecurity analyst trainee with practical experience in network vulnerability scanning and SIEM log analysis.", "label": "summary"},
            {"text": "CERTIFICATIONS", "label": "certifications"},
            {"text": "CompTIA Security+ (SY0-601) - Certified October 2023", "label": "certifications"},
            {"text": "Cisco Certified Support Technician (CCST) Cybersecurity - May 2023", "label": "certifications"},
            {"text": "AWS Certified Cloud Practitioner - January 2024", "label": "certifications"},
            {"text": "TECHNICAL SKILLS", "label": "skills"},
            {"text": "Security Tools: Wireshark, Nmap, Nessus, Splunk, Metasploit, Burp Suite", "label": "skills"},
            {"text": "Operating Systems & Networking: Linux (Kali), Windows Server, TCP/IP, Firewalls, Snort", "label": "skills"},
            {"text": "PRACTICAL EXPERIENCE", "label": "experience"},
            {"text": "Information Security Intern | ShieldGate Defense | June 2023 - Present", "label": "experience"},
            {"text": "Monitored security alerts in Splunk SIEM across 350 endpoints, triaging potential phishing events.", "label": "experience"},
            {"text": "Conducted internal vulnerability assessments using Nessus, documenting 14 high-severity CVEs.", "label": "experience"},
            {"text": "EDUCATION", "label": "education"},
            {"text": "Associate of Applied Science in Cybersecurity, Dallas College, Graduated May 2023", "label": "education"},
            {"text": "LAB PROJECTS", "label": "projects"},
            {"text": "Defensive Home Lab Infrastructure - Configured virtualized enterprise lab running pfSense firewall and Security Onion.", "label": "projects"}
        ]
    },
    {
        "document_id": "doc_07",
        "domain": "project_management",
        "items": [
            {"text": "ELENA ROSTOVA | New York, NY | elena.rostova@example.local", "label": "other"},
            {"text": "EXECUTIVE SUMMARY", "label": "summary"},
            {"text": "Results-driven Technical Project Manager with 7+ years leading cross-functional agile teams delivering software products.", "label": "summary"},
            {"text": "CORE COMPETENCIES", "label": "skills"},
            {"text": "Methodologies: Agile, Scrum, Kanban, Waterfall, SDLC, Sprint Planning", "label": "skills"},
            {"text": "Project Tools: Jira, Confluence, Asana, Monday.com, Trello, MS Project", "label": "skills"},
            {"text": "Strategy: Stakeholder Management, OKRs, Backlog Grooming, Risk Management", "label": "skills"},
            {"text": "PROFESSIONAL EXPERIENCE", "label": "experience"},
            {"text": "Senior Technical Project Manager | Finovate Technologies | September 2020 - Present", "label": "experience"},
            {"text": "Facilitated daily standups, sprint planning, and retrospective meetings for two distributed engineering squads.", "label": "experience"},
            {"text": "Delivered a core payment gateway integration on schedule and 8% under budget.", "label": "experience"},
            {"text": "CERTIFICATIONS & CREDENTIALS", "label": "certifications"},
            {"text": "Certified ScrumMaster (CSM) - Scrum Alliance, 2019", "label": "certifications"},
            {"text": "Project Management Professional (PMP) - PMI, 2021", "label": "certifications"},
            {"text": "EDUCATION", "label": "education"},
            {"text": "Bachelor of Business Administration in MIS, Pace University, 2016", "label": "education"}
        ]
    },
    {
        "document_id": "doc_08",
        "domain": "junior_developer",
        "items": [
            {"text": "TAYLOR BROOKS | Austin, TX | taylor.brooks@example.local", "label": "other"},
            {"text": "WORK EXPERIENCE", "label": "experience"},
            {"text": "Junior Python Developer | Local Tech Hub | 2023 - Present", "label": "experience"},
            {"text": "Helped build internal data entry tools using Python and SQLite. Fixed bug tickets and assisted with database maintenance.", "label": "experience"},
            {"text": "Wrote simple unit tests with pytest. Worked with Git for version control.", "label": "experience"},
            {"text": "SKILLS", "label": "skills"},
            {"text": "Python, SQLite, Git, HTML, Linux", "label": "skills"}
        ]
    },
    {
        "document_id": "doc_09",
        "domain": "devops_cloud",
        "items": [
            {"text": "DEVIN REED | Seattle, WA | devin.reed@example.local", "label": "other"},
            {"text": "SUMMARY", "label": "summary"},
            {"text": "DevOps Engineer specializing in Kubernetes infrastructure, CI/CD automation, and cloud security compliance.", "label": "summary"},
            {"text": "AREAS OF EXPERTISE", "label": "skills"},
            {"text": "Cloud Platforms: AWS (EKS, IAM, VPC), GCP, Terraform, Ansible", "label": "skills"},
            {"text": "Containers: Docker, Kubernetes, Helm, ArgoCD, Prometheus, Grafana", "label": "skills"},
            {"text": "Scripting: Python, Bash, Go", "label": "skills"},
            {"text": "EMPLOYMENT HISTORY", "label": "experience"},
            {"text": "Senior DevOps Engineer | CloudScale Inc | 2021 - Present", "label": "experience"},
            {"text": "Maintained multi-region Kubernetes clusters hosting 120+ microservices with 99.99% uptime.", "label": "experience"},
            {"text": "Automated infrastructure provisioning via Terraform and implemented GitOps workflows with ArgoCD.", "label": "experience"},
            {"text": "CERTIFICATIONS", "label": "certifications"},
            {"text": "Certified Kubernetes Administrator (CKA), Linux Foundation, 2022", "label": "certifications"},
            {"text": "AWS Certified Solutions Architect - Professional, 2023", "label": "certifications"},
            {"text": "ACADEMIC BACKGROUND", "label": "education"},
            {"text": "B.S. in Computer Network Security, Oregon State University, 2019", "label": "education"}
        ]
    },
    {
        "document_id": "doc_10",
        "domain": "mobile_developer",
        "items": [
            {"text": "CHLOE MARTINEZ | San Diego, CA | chloe.m@example.local", "label": "other"},
            {"text": "PROFESSIONAL PROFILE", "label": "summary"},
            {"text": "Mobile Application Developer with 4 years designing iOS and cross-platform mobile solutions with Flutter and Swift.", "label": "summary"},
            {"text": "TECHNICAL PROFICIENCIES", "label": "skills"},
            {"text": "Mobile: Flutter, Dart, Swift, SwiftUI, iOS SDK, Android SDK", "label": "skills"},
            {"text": "Tools & APIs: Firebase, REST APIs, SQLite, Git, Fastlane, Xcode", "label": "skills"},
            {"text": "RELEVANT EXPERIENCE", "label": "experience"},
            {"text": "Mobile App Developer | AppVenture Studios | 2021 - Present", "label": "experience"},
            {"text": "Published 3 consumer mobile applications to the Apple App Store and Google Play Store with over 200k downloads.", "label": "experience"},
            {"text": "Integrated offline caching using SQLite and real-time push notifications with Firebase Cloud Messaging.", "label": "experience"},
            {"text": "NOTABLE PROJECTS", "label": "projects"},
            {"text": "Fitness Habit Tracker - Cross-platform Flutter app featuring state management with BLoC and automated testing.", "label": "projects"},
            {"text": "EDUCATION", "label": "education"},
            {"text": "B.S. in Software Engineering, San Diego State University, 2020", "label": "education"}
        ]
    },
    {
        "document_id": "doc_11",
        "domain": "qa_automation",
        "items": [
            {"text": "VIKTOR NOVAK | Boston, MA | viktor.n@example.local", "label": "other"},
            {"text": "CAREER SUMMARY", "label": "summary"},
            {"text": "QA Automation Engineer with deep expertise in Cypress, Selenium, API testing, and performance validation.", "label": "summary"},
            {"text": "SKILLS MATRIX", "label": "skills"},
            {"text": "Test Automation: Cypress, Selenium WebDriver, Playwright, Jest, Pytest", "label": "skills"},
            {"text": "API & Performance Testing: Postman, JMeter, REST Assured, K6", "label": "skills"},
            {"text": "EXPERIENCE SUMMARY", "label": "experience"},
            {"text": "Senior QA Engineer | QualiTech Systems | 2020 - Present", "label": "experience"},
            {"text": "Developed test automation frameworks in TypeScript and Cypress, cutting regression cycle time from 3 days to 4 hours.", "label": "experience"},
            {"text": "Integrated automated test suites into GitLab CI/CD pipelines with failure alert webhooks.", "label": "experience"},
            {"text": "PROJECTS", "label": "projects"},
            {"text": "Automated Performance Benchmark Harness - Python and K6 load testing utility measuring API latency under stress.", "label": "projects"},
            {"text": "EDUCATION", "label": "education"},
            {"text": "B.S. in Computer Science, Northeastern University, 2018", "label": "education"},
            {"text": "CERTIFICATIONS", "label": "certifications"},
            {"text": "ISTQB Certified Tester Foundation Level (CTFL), 2019", "label": "certifications"}
        ]
    },
    {
        "document_id": "doc_12",
        "domain": "data_engineering",
        "items": [
            {"text": "ANANYA IYER | Atlanta, GA | ananya.iyer@example.local", "label": "other"},
            {"text": "OBJECTIVE STATEMENT", "label": "summary"},
            {"text": "Data Engineer committed to designing fault-tolerant real-time data pipelines and scalable analytics infrastructure.", "label": "summary"},
            {"text": "TECHNICAL SKILLS", "label": "skills"},
            {"text": "Big Data: Apache Spark, Kafka, Apache Airflow, Hadoop, Hive", "label": "skills"},
            {"text": "Databases & Clouds: PostgreSQL, Cassandra, AWS Redshift, Snowflake, S3", "label": "skills"},
            {"text": "Languages: Python, Scala, SQL, Bash", "label": "skills"},
            {"text": "PROFESSIONAL BACKGROUND", "label": "experience"},
            {"text": "Data Pipeline Engineer | Metro Analytics Hub | 2021 - Present", "label": "experience"},
            {"text": "Built streaming ingestion pipelines using Apache Kafka and Spark Streaming processing 15M records daily.", "label": "experience"},
            {"text": "Orchestrated complex DAG workflows in Apache Airflow with automated retry and backfill logic.", "label": "experience"},
            {"text": "EDUCATION & DEGREES", "label": "education"},
            {"text": "M.S. in Computer Science, Georgia Institute of Technology, 2021", "label": "education"},
            {"text": "B.E. in Information Technology, Anna University, 2019", "label": "education"},
            {"text": "KEY ACHIEVEMENTS & PROJECTS", "label": "projects"},
            {"text": "Lakehouse Schema Evolution Manager - Tool to track Delta Lake schema changes and alert downstream consumers.", "label": "projects"}
        ]
    },
    {
        "document_id": "doc_13",
        "domain": "fullstack_engineering",
        "items": [
            {"text": "DANIEL KIM | Los Angeles, CA | daniel.kim@example.local", "label": "other"},
            {"text": "SUMMARY", "label": "summary"},
            {"text": "Full-Stack Engineer with proficiency in React, Node.js, and relational database systems.", "label": "summary"},
            {"text": "TECHNICAL COMPETENCIES", "label": "skills"},
            {"text": "Frontend: React, Redux, Next.js, HTML5, CSS3, Tailwind CSS", "label": "skills"},
            {"text": "Backend: Node.js, Express, Python, Django, REST APIs, GraphQL", "label": "skills"},
            {"text": "Databases & Tools: PostgreSQL, MongoDB, Docker, Git, Jest", "label": "skills"},
            {"text": "WORK EXPERIENCE", "label": "experience"},
            {"text": "Full Stack Developer | Nexa Digital Solutions | 2022 - Present", "label": "experience"},
            {"text": "Constructed responsive web portals utilizing React, TypeScript, and Express.js backend services.", "label": "experience"},
            {"text": "Authored database migration scripts for PostgreSQL and reduced API response times through Redis caching.", "label": "experience"},
            {"text": "PROJECTS", "label": "projects"},
            {"text": "Collaborative Whiteboard App - Real-time canvas application built using WebSockets, React, and Node.js.", "label": "projects"},
            {"text": "EDUCATION", "label": "education"},
            {"text": "B.S. in Computer Science, UCLA, 2022", "label": "education"}
        ]
    },
    {
        "document_id": "doc_14",
        "domain": "product_management",
        "items": [
            {"text": "SARAH JENKINS | Seattle, WA | sarah.j@example.local", "label": "other"},
            {"text": "PROFESSIONAL PROFILE", "label": "summary"},
            {"text": "Product Manager with 6 years leading enterprise SaaS products from ideation to general availability.", "label": "summary"},
            {"text": "CORE SKILLS", "label": "skills"},
            {"text": "Product Strategy: Product Discovery, User Research, Roadmapping, PRDs, Customer Interviews", "label": "skills"},
            {"text": "Analytics & Tools: Amplitude, Mixpanel, SQL, Jira, Confluence, Figma", "label": "skills"},
            {"text": "PROFESSIONAL EXPERIENCE", "label": "experience"},
            {"text": "Senior Product Manager | CloudConnect | 2020 - Present", "label": "experience"},
            {"text": "Led cross-functional team of 12 engineers and 2 product designers to launch enterprise billing platform.", "label": "experience"},
            {"text": "Grew annual recurring revenue (ARR) from $2.1M to $8.5M over two fiscal years.", "label": "experience"},
            {"text": "EDUCATION", "label": "education"},
            {"text": "B.A. in Economics & Information Science, University of Washington, 2017", "label": "education"},
            {"text": "CERTIFICATIONS", "label": "certifications"},
            {"text": "Pragmatic Institute Certified (PMC-III), 2021", "label": "certifications"}
        ]
    },
    {
        "document_id": "doc_15",
        "domain": "systems_embedded",
        "items": [
            {"text": "LUCAS SILVA | San Jose, CA | lucas.s@example.local", "label": "other"},
            {"text": "SUMMARY STATEMENT", "label": "summary"},
            {"text": "Embedded Systems Engineer focused on low-power firmware development, RTOS kernels, and hardware communication protocols.", "label": "summary"},
            {"text": "SKILLS", "label": "skills"},
            {"text": "Firmware & Languages: C, C++, Assembly, FreeRTOS, Embedded Linux", "label": "skills"},
            {"text": "Protocols & Hardware: I2C, SPI, UART, CAN bus, Oscilloscopes, Logic Analyzers", "label": "skills"},
            {"text": "WORK EXPERIENCE", "label": "experience"},
            {"text": "Firmware Engineer | IoT Sensor Networks | 2021 - Present", "label": "experience"},
            {"text": "Developed device drivers and power management algorithms in C for ARM Cortex-M microcontrollers.", "label": "experience"},
            {"text": "Reduced sleep mode current consumption by 40%, extending battery life of sensor nodes to 3 years.", "label": "experience"},
            {"text": "PROJECTS", "label": "projects"},
            {"text": "Custom RTOS Scheduler - Designed round-robin task scheduler on STM32 microcontroller.", "label": "projects"},
            {"text": "EDUCATION", "label": "education"},
            {"text": "B.S. in Electrical and Computer Engineering, San Jose State University, 2020", "label": "education"}
        ]
    },
    {
        "document_id": "doc_16",
        "domain": "ai_research",
        "items": [
            {"text": "DR. MAYA LIN | Cambridge, MA | maya.lin@example.local", "label": "other"},
            {"text": "RESEARCH SUMMARY", "label": "summary"},
            {"text": "Machine Learning Researcher investigating multilingual NLP, self-supervised representation learning, and model interpretability.", "label": "summary"},
            {"text": "TECHNICAL PROFICIENCIES", "label": "skills"},
            {"text": "Frameworks: PyTorch, JAX, Hugging Face Transformers, DeepSpeed, Ray", "label": "skills"},
            {"text": "Languages & Tools: Python, C++, CUDA, Git, Linux, Slurm HPC clusters", "label": "skills"},
            {"text": "RESEARCH EXPERIENCE", "label": "experience"},
            {"text": "Postdoctoral Researcher | MIT CSAIL | 2022 - Present", "label": "experience"},
            {"text": "Published 4 first-author papers in ACL and NeurIPS exploring attention mechanism efficiency.", "label": "experience"},
            {"text": "Mentored 3 graduate researchers on multi-task learning benchmarks.", "label": "experience"},
            {"text": "EDUCATION", "label": "education"},
            {"text": "Ph.D. in Computer Science, Carnegie Mellon University, 2022", "label": "education"},
            {"text": "B.S. in Mathematics and Computer Science, Stanford University, 2017", "label": "education"},
            {"text": "RESEARCH PROJECTS", "label": "projects"},
            {"text": "Cross-Lingual Embedding Benchmark - Evaluated representations across 45 low-resource language pairs.", "label": "projects"}
        ]
    }
]

# Ground-truth evaluation dataset for skill extraction
SKILL_EXTRACTION_EVAL_DATA = [
    {
        "id": "skill_eval_01",
        "text": "Designed REST APIs using FastAPI, PostgreSQL, and Docker deployed on AWS.",
        "ground_truth_skills": ["RESTful APIs", "FastAPI", "PostgreSQL", "Docker", "AWS"]
    },
    {
        "id": "skill_eval_02",
        "text": "Engineered automated ETL pipelines in dbt, BigQuery, and Apache Airflow with SQL queries.",
        "ground_truth_skills": ["dbt", "Google BigQuery", "Apache Airflow", "SQL"]
    },
    {
        "id": "skill_eval_03",
        "text": "Fine-tuned BERT transformers using PyTorch and Hugging Face for token classification with spaCy.",
        "ground_truth_skills": ["Hugging Face Transformers", "PyTorch", "Natural Language Processing"]
    },
    {
        "id": "skill_eval_04",
        "text": "Built responsive user interfaces in React, TypeScript, Next.js, and Tailwind CSS.",
        "ground_truth_skills": ["React", "TypeScript", "Next.js", "Tailwind CSS"]
    },
    {
        "id": "skill_eval_05",
        "text": "Implemented distributed event streaming with Apache Kafka, Go, and Redis clusters.",
        "ground_truth_skills": ["Apache Kafka", "Go", "Redis"]
    },
    {
        "id": "skill_eval_06",
        "text": "Triaged security incidents in Splunk SIEM and scanned network hosts using Wireshark and Nessus.",
        "ground_truth_skills": ["Splunk", "Wireshark", "Nessus"]
    },
    {
        "id": "skill_eval_07",
        "text": "Facilitated Agile sprint planning, Kanban boards, and Jira ticket roadmaps.",
        "ground_truth_skills": ["Agile", "Scrum", "Kanban", "Jira"]
    },
    {
        "id": "skill_eval_08",
        "text": "Wrote comprehensive unit and regression tests in Python using Pytest and Git for version control.",
        "ground_truth_skills": ["Python", "Pytest", "Git"]
    }
]

# Labeled resume-to-job pairs for retrieval / matching evaluation
# Each pair has a human-reviewed relevance score (0: Irrelevant, 1: Weak, 2: Moderate, 3: Strong Match)
MATCHING_EVAL_PAIRS = [
    {
        "id": "pair_01",
        "resume_domain": "software_engineering",
        "job_title": "Backend Engineer (Python / Go / AWS)",
        "relevance_score": 3,
        "is_relevant": 1,
        "resume_sample": "Alex Chen, Software Engineer. Experience with FastAPI, Python, PostgreSQL, Redis, Docker, AWS.",
        "job_sample": "Seeking Backend Engineer proficient in Python, Go, FastAPI, PostgreSQL, Redis, and AWS cloud."
    },
    {
        "id": "pair_02",
        "resume_domain": "software_engineering",
        "job_title": "Data Analyst (SQL / BI / Product Analytics)",
        "relevance_score": 1,
        "is_relevant": 0,
        "resume_sample": "Alex Chen, Software Engineer. Experience with FastAPI, Python, PostgreSQL, Redis, Docker, AWS.",
        "job_sample": "Hiring Data Analyst with advanced SQL, Tableau, Power BI, and product A/B testing experience."
    },
    {
        "id": "pair_03",
        "resume_domain": "data_analytics",
        "job_title": "Data Analyst (SQL / BI / Product Analytics)",
        "relevance_score": 3,
        "is_relevant": 1,
        "resume_sample": "Jordan Taylor, Data Analyst. Experience with SQL, Tableau, BigQuery, dbt, A/B testing, and Pandas.",
        "job_sample": "Hiring Data Analyst with advanced SQL, Tableau, Power BI, and product A/B testing experience."
    },
    {
        "id": "pair_04",
        "resume_domain": "data_analytics",
        "job_title": "Frontend Engineer (React / TypeScript)",
        "relevance_score": 0,
        "is_relevant": 0,
        "resume_sample": "Jordan Taylor, Data Analyst. Experience with SQL, Tableau, BigQuery, dbt, A/B testing, and Pandas.",
        "job_sample": "Looking for Frontend Engineer with React, TypeScript, Next.js, and CSS design systems."
    },
    {
        "id": "pair_05",
        "resume_domain": "machine_learning",
        "job_title": "Machine Learning Engineer (NLP / PyTorch)",
        "relevance_score": 3,
        "is_relevant": 1,
        "resume_sample": "Samira Khan, ML Intern. Research in PyTorch, NLP, BERT transformers, and LoRA fine-tuning.",
        "job_sample": "Join AI team. Requires PyTorch, Transformers, NLP evaluation, model fine-tuning, and Docker."
    },
    {
        "id": "pair_06",
        "resume_domain": "machine_learning",
        "job_title": "Senior Technical Project Manager",
        "relevance_score": 0,
        "is_relevant": 0,
        "resume_sample": "Samira Khan, ML Intern. Research in PyTorch, NLP, BERT transformers, and LoRA fine-tuning.",
        "job_sample": "Seeking Technical Project Manager with Agile, Scrum, Jira, and enterprise stakeholder alignment."
    },
    {
        "id": "pair_07",
        "resume_domain": "frontend_engineering",
        "job_title": "Frontend Engineer (React / TypeScript)",
        "relevance_score": 3,
        "is_relevant": 1,
        "resume_sample": "Liam O'Connor, Frontend Engineer. React, TypeScript, Next.js, Tailwind CSS, Jest, Cypress.",
        "job_sample": "Looking for Frontend Engineer with React, TypeScript, Next.js, and CSS design systems."
    },
    {
        "id": "pair_08",
        "resume_domain": "frontend_engineering",
        "job_title": "Backend Engineer (Python / Go / AWS)",
        "relevance_score": 1,
        "is_relevant": 0,
        "resume_sample": "Liam O'Connor, Frontend Engineer. React, TypeScript, Next.js, Tailwind CSS, Jest, Cypress.",
        "job_sample": "Seeking Backend Engineer proficient in Python, Go, FastAPI, PostgreSQL, Redis, and AWS cloud."
    },
    {
        "id": "pair_09",
        "resume_domain": "backend_engineering",
        "job_title": "Backend Engineer (Python / Go / AWS)",
        "relevance_score": 3,
        "is_relevant": 1,
        "resume_sample": "Marcus Vance, Backend Engineer. Go, gRPC, Apache Kafka, PostgreSQL, Redis, GCP, Kubernetes.",
        "job_sample": "Seeking Backend Engineer proficient in Python, Go, FastAPI, PostgreSQL, Redis, and AWS cloud."
    },
    {
        "id": "pair_10",
        "resume_domain": "project_management",
        "job_title": "Senior Technical Project Manager",
        "relevance_score": 3,
        "is_relevant": 1,
        "resume_sample": "Elena Rostova, Technical Project Manager. Agile, Scrum, Jira, PMP, stakeholder management.",
        "job_sample": "Seeking Technical Project Manager with Agile, Scrum, Jira, and enterprise stakeholder alignment."
    },
    {
        "id": "pair_11",
        "resume_domain": "cybersecurity",
        "job_title": "Cybersecurity Analyst Trainee",
        "relevance_score": 3,
        "is_relevant": 1,
        "resume_sample": "Priya Patel, Cybersecurity Trainee. CompTIA Security+, Splunk, Wireshark, Nessus, Linux.",
        "job_sample": "Entry-level Cybersecurity Analyst needed for SIEM log monitoring, vulnerability scanning, and Wireshark."
    },
    {
        "id": "pair_12",
        "resume_domain": "cybersecurity",
        "job_title": "Data Analyst (SQL / BI / Product Analytics)",
        "relevance_score": 0,
        "is_relevant": 0,
        "resume_sample": "Priya Patel, Cybersecurity Trainee. CompTIA Security+, Splunk, Wireshark, Nessus, Linux.",
        "job_sample": "Hiring Data Analyst with advanced SQL, Tableau, Power BI, and product A/B testing experience."
    }
]


def normalize_text(text: str) -> str:
    """Normalizes whitespace and removes unwanted control characters while preserving casing and symbols."""
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def mask_personal_identifiers(text: str) -> str:
    """Masks emails and phone numbers for privacy safeguards."""
    # Mask email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', text)
    # Mask phone numbers
    text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '[REDACTED_PHONE]', text)
    return text


def prepare_datasets(output_dir: str = "data/processed", results_dir: str = "results", random_seed: int = 42):
    """
    Processes annotations, splits documents into train/val/test splits without leakage,
    and produces summary statistics.
    """
    random.seed(random_seed)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs("data/raw", exist_ok=True)

    # 1. Save raw annotated documents
    with open("data/raw/raw_section_data.json", "w", encoding="utf-8") as f:
        json.dump(ANNOTATED_DOCUMENTS, f, indent=2)

    with open("data/raw/skill_extraction_eval.json", "w", encoding="utf-8") as f:
        json.dump(SKILL_EXTRACTION_EVAL_DATA, f, indent=2)

    with open("data/raw/matching_eval_pairs.json", "w", encoding="utf-8") as f:
        json.dump(MATCHING_EVAL_PAIRS, f, indent=2)

    # 2. Extract rows with document grouping
    rows = []
    for doc in ANNOTATED_DOCUMENTS:
        doc_id = doc["document_id"]
        domain = doc.get("domain", "general")
        for item in doc["items"]:
            clean_text = normalize_text(item["text"])
            safe_text = mask_personal_identifiers(clean_text)
            label = item["label"].lower().strip()
            rows.append({
                "document_id": doc_id,
                "domain": domain,
                "text": safe_text,
                "label": label
            })

    df = pd.DataFrame(rows)

    # Validate non-empty
    assert len(df) > 0, "Dataset cannot be empty"
    assert not df["text"].isnull().any(), "Found null text entries"
    assert not df["label"].isnull().any(), "Found null label entries"

    # 3. Document-level split (Anti-Leakage Guarantee)
    doc_ids = list(df["document_id"].unique())
    random.shuffle(doc_ids)

    # 70% train, 15% val, 15% test
    n_train = max(1, int(len(doc_ids) * 0.70))
    n_val = max(1, int(len(doc_ids) * 0.15))

    train_docs = doc_ids[:n_train]
    val_docs = doc_ids[n_train:n_train + n_val]
    test_docs = doc_ids[n_train + n_val:]

    train_df = df[df["document_id"].isin(train_docs)].copy()
    val_df = df[df["document_id"].isin(val_docs)].copy()
    test_df = df[df["document_id"].isin(test_docs)].copy()

    # Save processed splits
    train_df.to_csv(os.path.join(output_dir, "section_train.csv"), index=False)
    val_df.to_csv(os.path.join(output_dir, "section_val.csv"), index=False)
    test_df.to_csv(os.path.join(output_dir, "section_test.csv"), index=False)

    # Save eval datasets in processed dir as well
    with open(os.path.join(output_dir, "skill_extraction_eval.json"), "w", encoding="utf-8") as f:
        json.dump(SKILL_EXTRACTION_EVAL_DATA, f, indent=2)

    with open(os.path.join(output_dir, "matching_eval_pairs.json"), "w", encoding="utf-8") as f:
        json.dump(MATCHING_EVAL_PAIRS, f, indent=2)

    # 4. Generate dataset summary report
    label_distribution = df["label"].value_counts().to_dict()
    split_counts = {
        "train": len(train_df),
        "val": len(val_df),
        "test": len(test_df),
        "total_lines": len(df),
        "total_documents": len(doc_ids),
        "train_documents": train_docs,
        "val_documents": val_docs,
        "test_documents": test_docs
    }

    summary = {
        "dataset_name": "ResumeLens Curated Resume Section & Evaluation Corpus",
        "version": "1.0.0",
        "description": "Synthetically authored and curated resume sections, skill spans, and matching pairs for reproducible ML development.",
        "license": "Creative Commons Zero (CC0 1.0 Universal) - Public Domain",
        "random_seed": random_seed,
        "total_documents": len(doc_ids),
        "total_labeled_lines": len(df),
        "classes": list(df["label"].unique()),
        "label_distribution": label_distribution,
        "split_counts": split_counts,
        "skill_eval_samples": len(SKILL_EXTRACTION_EVAL_DATA),
        "matching_eval_pairs": len(MATCHING_EVAL_PAIRS),
        "anti_leakage": "Split performed strictly at document_id level. Zero document overlap across train, val, and test.",
        "pii_safeguards": "All direct identifiers (emails, phones) masked or synthetic."
    }

    with open(os.path.join(results_dir, "dataset_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Data preparation complete!")
    print(f"Total lines: {len(df)} across {len(doc_ids)} documents.")
    print(f"Train lines: {len(train_df)} | Val lines: {len(val_df)} | Test lines: {len(test_df)}")
    print(f"Classes: {label_distribution}")
    print(f"Saved dataset summary to {os.path.join(results_dir, 'dataset_summary.json')}")

    return summary


if __name__ == "__main__":
    prepare_datasets()
