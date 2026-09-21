# Project Report: Unified Academic & Career Preparation Platform

*(This document provides a copy-paste ready structure for your final university project report.)*

## 1. Introduction
*   **Problem Statement**: Students often juggle multiple disconnected platforms for academic tracking (LMS), coding practice (LeetCode), and career preparation (Resume building).
*   **Proposed Solution**: A single, unified platform that integrates academic performance tracking, sandboxed coding practice, and AI-powered career matching based on resume extraction.

## 2. Objectives
1.  Develop a secure authentication system with role-based access.
2.  Implement an Academic Dashboard to track subjects, attendance, assignments, and exam marks.
3.  Build a safe, sandboxed Code Execution engine for algorithm practice.
4.  Integrate a Large Language Model (Gemini) to provide PII-scrubbed resume feedback.
5.  Create a deterministic skill-to-career matching algorithm.

## 3. System Architecture
*   **Frontend**: HTML/CSS/JS (Vanilla), Chart.js for data visualization, Lucide for iconography.
*   **Backend**: Python Flask framework using Blueprints for modularity (`auth`, `academics`, `coding`, `resume`, `career`, `ai`).
*   **Database**: SQLite with `sqlite3` driver. Relational tables for Users, Subjects, Marks, Submissions, Resumes, and Extracted Entities.
*   **Security Layer**:
    *   Flask-WTF for CSRF protection on all state-changing forms.
    *   Werkzeug for password hashing (`pbkdf2:sha256`) and secure file names.
    *   Strict parameter scoping to prevent Insecure Direct Object Reference (IDOR).
    *   Subprocess isolation with strict timeouts for code execution.

## 4. Implementation Details (Module by Module)
*   **Authentication**: Session-based login using Flask-Login.
*   **Academics Module**: CRUD operations for student records.
*   **Coding Sandbox**: Uses `subprocess.run` with stripped environment variables (`PYTHONDONTWRITEBYTECODE`, `PYTHONIOENCODING`) and a 5-second timeout to prevent resource exhaustion and RCE (Remote Code Execution).
*   **AI Integration**: 
    *   Uses PyMuPDF to extract text.
    *   Applies regex to scrub PII (emails, phone numbers, URLs).
    *   Calls Google Gemini 1.5 Flash.
    *   Caches responses in `ai_insights_cache` to reduce API latency and cost.
    *   Sanitizes markdown output using `DOMPurify` to prevent XSS.

## 5. Security & Testing
*   **File Uploads**: Validates both the file extension (`.pdf`) and the actual magic bytes (`%PDF-`) before saving.
*   **Automated Testing**: Pytest suite verifying auth flows, database roundtrips, and sandbox timeouts.
*   **Error Handling**: Graceful fallback UI for missing data and custom 404/500 error pages to prevent stack-trace exposure.

## 6. Conclusion and Future Scope
*   **Conclusion**: The platform successfully achieves a holistic view of a student's profile, merging academics with practical skills.
*   **Future Scope**: Support for multiple programming languages (Java, C++), integration with external job boards, and automated PDF generation of the student's unified portfolio.
