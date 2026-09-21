# Educational Platform: Mini Project

A unified academic and career preparation platform for students. This application provides a comprehensive suite of tools for students to manage their academic progress, practice coding interviews in a sandboxed environment, analyze their resumes using AI, and match with career roles.

## Features

*   **Academic Dashboard**: Track subjects, assignments, attendance, and exam marks.
*   **Coding Platform**: Practice programming problems with a secure, sandboxed execution environment (timeout and process isolation).
*   **AI Resume Analyzer**: Upload a PDF resume to extract skills, education, and experience. Receive Gemini-powered AI feedback and scoring (PII-scrubbed for privacy).
*   **Career Role Matching**: Match extracted skills against predefined career roles to identify skill gaps and recommended learning paths.
*   **Unified Dashboard**: A beautiful, single-page view summarizing upcoming assignments, coding progress, and AI career insights.

## Technology Stack

*   **Backend**: Python, Flask, SQLite (Database)
*   **Frontend**: HTML5, CSS3, Vanilla JavaScript, Chart.js, Lucide Icons
*   **AI Integration**: Google Gemini 1.5 Flash (via `google-generativeai`)
*   **Security**: Werkzeug (Password Hashing, Secure Filenames), Flask-WTF (CSRF Protection), DOMPurify (XSS Prevention)
*   **Testing**: Pytest

## Architecture & Security

*   **Modular Blueprints**: The app is divided into functional blueprints (`auth`, `academics`, `coding`, `resume`, `career`, `ai`).
*   **Sandboxed Execution**: Student code submissions are executed in an isolated `subprocess` with a strict 5-second timeout and stripped environment variables to prevent RCE.
*   **AI Caching & Privacy**: AI insights are cached in `ai_insights_cache` to reduce API calls. Resume text is aggressively scrubbed of PII (emails, phone numbers, URLs) before being sent to the LLM.
*   **Robust Authorization**: All parameterized routes are audited for IDOR (Insecure Direct Object Reference) to ensure students can only view/modify their own data.

## Installation

1. Clone the repository and navigate to the project directory.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set environment variables:
   ```bash
   set SECRET_KEY=your_secure_secret_key
   set GEMINI_API_KEY=your_gemini_api_key
   ```
5. Run the application:
   ```bash
   python app.py
   ```

## Testing

Run the automated test suite using pytest:
```bash
pytest tests/ -v
```

## Demo Credentials

Upon the first run, the database is automatically seeded.
**Admin Account**: `admin` / `admin123`
*(Create a new student account to explore the dashboard and features).*
