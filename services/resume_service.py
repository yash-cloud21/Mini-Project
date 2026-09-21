import os
import re
import pymupdf as fitz  # PyMuPDF
from werkzeug.utils import secure_filename
from database.db import get_db

SKILL_DICTIONARY = {
    'programming_languages': ['python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'ruby', 'go', 'swift', 'kotlin', 'php', 'rust', 'sql'],
    'frameworks': ['flask', 'django', 'react', 'angular', 'vue', 'spring', 'express', 'nodejs', 'node.js', 'laravel', 'rubyonrails', 'ruby on rails'],
    'databases': ['mysql', 'postgresql', 'sqlite', 'mongodb', 'redis', 'cassandra', 'oracle', 'sql server'],
    'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'heroku', 'digitalocean'],
    'tools': ['git', 'github', 'gitlab', 'bitbucket', 'jira', 'linux', 'jenkins', 'ci/cd', 'webpack', 'babel'],
    'ml_data': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'keras', 'pytorch', 'matplotlib', 'seaborn', 'hadoop', 'spark'],
    'soft_skills': ['communication', 'teamwork', 'leadership', 'problem solving', 'agile', 'scrum', 'time management']
}

def extract_text_from_pdf(filepath):
    text = ""
    try:
        doc = fitz.open(filepath)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text

def extract_skills(text):
    extracted_skills = []
    text_lower = text.lower()
    
    # We use regex to find whole word matches
    for category, skills in SKILL_DICTIONARY.items():
        for skill in skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                extracted_skills.append({
                    'category': category,
                    'skill': skill.title()
                })
    return extracted_skills

def extract_education(text):
    education = []
    # Basic heuristic: look for degree keywords
    degrees = ['b.tech', 'btech', 'b.e.', 'bachelor', 'master', 'm.tech', 'mtech', 'phd', 'b.sc', 'm.sc']
    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower()
        for degree in degrees:
            if degree in line_lower:
                # Add basic entry, more sophisticated NLP would be needed for institution/year
                education.append({
                    'degree': line.strip(),
                    'institution': 'Extracted from text',
                    'year': ''
                })
                break # Only add the line once
    
    # Deduplicate and limit
    return education[:3]

def extract_experience(text):
    experience = []
    # Look for "Experience" section
    text_lower = text.lower()
    exp_idx = text_lower.find('experience')
    if exp_idx != -1:
        # Extract a snippet after the word "experience"
        snippet = text[exp_idx:exp_idx+500]
        lines = snippet.split('\n')
        # Skip the header line itself
        for line in lines[1:]:
            if line.strip() and len(line.strip()) > 5:
                experience.append({
                    'role': 'Extracted Experience',
                    'company': line.strip()[:100],
                    'duration': '',
                    'description': ''
                })
                if len(experience) >= 2:
                    break
    return experience

def extract_projects(text):
    projects = []
    text_lower = text.lower()
    proj_idx = text_lower.find('project')
    if proj_idx != -1:
        snippet = text[proj_idx:proj_idx+500]
        lines = snippet.split('\n')
        for line in lines[1:]:
            if line.strip() and len(line.strip()) > 5:
                projects.append({
                    'title': line.strip()[:100],
                    'description': 'Extracted from Projects section'
                })
                if len(projects) >= 2:
                    break
    return projects

def process_resume(user_id, file, upload_folder):
    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.pdf'):
        raise ValueError("Only PDF files are allowed.")
        
    # Security: Verify actual file content (Magic Bytes)
    header = file.read(5)
    file.seek(0) # Reset file pointer after reading
    if header != b'%PDF-':
        raise ValueError("Invalid file content. Expected a valid PDF document.")
        
    # Ensure filename is unique for the user to prevent overwrites
    import time
    unique_filename = f"{user_id}_{int(time.time())}_{filename}"
    file_path = os.path.join(upload_folder, unique_filename)
    
    file.save(file_path)
    
    # Extract text
    raw_text = extract_text_from_pdf(file_path)
    if not raw_text.strip():
        raise ValueError("Could not extract text from the PDF. It may be scanned or empty.")
        
    # Extract entities
    skills = extract_skills(raw_text)
    education = extract_education(raw_text)
    experience = extract_experience(raw_text)
    projects = extract_projects(raw_text)
    
    # Save to database
    db = get_db()
    
    # 1. Save Resume metadata
    cursor = db.execute(
        "INSERT INTO resumes (user_id, filename, original_filename, file_path, raw_text) VALUES (?, ?, ?, ?, ?)",
        (user_id, unique_filename, file.filename, file_path, raw_text)
    )
    resume_id = cursor.lastrowid
    
    # 2. Save Skills
    for skill in skills:
        db.execute(
            "INSERT INTO extracted_skills (resume_id, skill_category, skill_name) VALUES (?, ?, ?)",
            (resume_id, skill['category'], skill['skill'])
        )
        
    # 3. Save Education
    for edu in education:
        db.execute(
            "INSERT INTO extracted_education (resume_id, institution, degree, year) VALUES (?, ?, ?, ?)",
            (resume_id, edu['institution'], edu['degree'], edu['year'])
        )
        
    # 4. Save Experience
    for exp in experience:
        db.execute(
            "INSERT INTO extracted_experience (resume_id, company, role, duration, description) VALUES (?, ?, ?, ?, ?)",
            (resume_id, exp['company'], exp['role'], exp['duration'], exp['description'])
        )
        
    # 5. Save Projects
    for proj in projects:
        db.execute(
            "INSERT INTO extracted_projects (resume_id, title, description) VALUES (?, ?, ?)",
            (resume_id, proj['title'], proj['description'])
        )
        
    db.commit()
    return resume_id

def get_user_resumes(user_id):
    db = get_db()
    resumes = db.execute(
        "SELECT * FROM resumes WHERE user_id = ? ORDER BY upload_date DESC",
        (user_id,)
    ).fetchall()
    return [dict(r) for r in resumes]

def get_resume_details(resume_id, user_id):
    db = get_db()
    resume = db.execute(
        "SELECT * FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, user_id)
    ).fetchone()
    
    if not resume:
        return None
        
    resume_dict = dict(resume)
    
    skills = db.execute("SELECT * FROM extracted_skills WHERE resume_id = ?", (resume_id,)).fetchall()
    resume_dict['skills'] = [dict(s) for s in skills]
    
    education = db.execute("SELECT * FROM extracted_education WHERE resume_id = ?", (resume_id,)).fetchall()
    resume_dict['education'] = [dict(e) for e in education]
    
    experience = db.execute("SELECT * FROM extracted_experience WHERE resume_id = ?", (resume_id,)).fetchall()
    resume_dict['experience'] = [dict(e) for e in experience]
    
    projects = db.execute("SELECT * FROM extracted_projects WHERE resume_id = ?", (resume_id,)).fetchall()
    resume_dict['projects'] = [dict(p) for p in projects]
    
    return resume_dict
