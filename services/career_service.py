from database.db import get_db

PREDEFINED_ROLES = [
    {
        'title': 'Python Developer',
        'description': 'Develops backend applications and scripts using Python.',
        'skills': ['Python', 'Django', 'Flask', 'SQL', 'Git', 'Linux']
    },
    {
        'title': 'Backend Developer',
        'description': 'Builds server-side logic, databases, and APIs.',
        'skills': ['Python', 'Java', 'Node.js', 'SQL', 'MongoDB', 'Docker', 'AWS']
    },
    {
        'title': 'Full Stack Developer',
        'description': 'Develops both client and server software.',
        'skills': ['JavaScript', 'React', 'Node.js', 'Python', 'SQL', 'Git', 'HTML', 'CSS']
    },
    {
        'title': 'Data Analyst',
        'description': 'Analyzes data sets to help companies make business decisions.',
        'skills': ['Python', 'Pandas', 'SQL', 'Excel', 'Tableau', 'Statistics']
    },
    {
        'title': 'Data Scientist',
        'description': 'Uses scientific methods and algorithms to extract knowledge from data.',
        'skills': ['Python', 'R', 'Machine Learning', 'Pandas', 'NumPy', 'Scikit-learn', 'SQL']
    },
    {
        'title': 'Machine Learning Engineer',
        'description': 'Builds and deploys machine learning models.',
        'skills': ['Python', 'TensorFlow', 'PyTorch', 'Machine Learning', 'Docker', 'AWS']
    },
    {
        'title': 'Software Developer',
        'description': 'General software engineering and application development.',
        'skills': ['Java', 'C++', 'Python', 'Git', 'Algorithms', 'Data Structures']
    },
    {
        'title': 'QA/Automation Engineer',
        'description': 'Designs and writes programs that run automatic tests on new or existing software.',
        'skills': ['Python', 'Java', 'Selenium', 'Jenkins', 'Git', 'Testing']
    }
]

def seed_job_roles():
    db = get_db()
    existing_roles = db.execute("SELECT COUNT(*) FROM job_roles").fetchone()[0]
    
    if existing_roles == 0:
        for role in PREDEFINED_ROLES:
            cursor = db.execute(
                "INSERT INTO job_roles (title, description) VALUES (?, ?)",
                (role['title'], role['description'])
            )
            role_id = cursor.lastrowid
            
            for skill in role['skills']:
                db.execute(
                    "INSERT INTO job_skills (role_id, skill_name) VALUES (?, ?)",
                    (role_id, skill.lower()) # Store target skills in lowercase for matching
                )
        db.commit()
        print("  [OK] Seeded predefined job roles")

def get_all_roles():
    db = get_db()
    roles = db.execute("SELECT * FROM job_roles ORDER BY title").fetchall()
    return [dict(r) for r in roles]

def get_target_role(user_id):
    db = get_db()
    target = db.execute("""
        SELECT jr.id, jr.title, jr.description
        FROM student_target_role str
        JOIN job_roles jr ON str.role_id = jr.id
        WHERE str.user_id = ?
    """, (user_id,)).fetchone()
    
    if target:
        return dict(target)
    return None

def set_target_role(user_id, role_id):
    db = get_db()
    # Check if a target role already exists
    existing = db.execute("SELECT id FROM student_target_role WHERE user_id = ?", (user_id,)).fetchone()
    
    if existing:
        db.execute("UPDATE student_target_role SET role_id = ?, selected_at = CURRENT_TIMESTAMP WHERE user_id = ?", (role_id, user_id))
    else:
        db.execute("INSERT INTO student_target_role (user_id, role_id) VALUES (?, ?)", (user_id, role_id))
        
    db.commit()

def analyze_skill_gap(user_id):
    db = get_db()
    
    target_role = get_target_role(user_id)
    if not target_role:
        return {'status': 'no_target_role'}
        
    # Get required skills for this role
    required_skills_rows = db.execute("SELECT skill_name FROM job_skills WHERE role_id = ?", (target_role['id'],)).fetchall()
    required_skills = [r['skill_name'].lower() for r in required_skills_rows]
    
    # Get user's extracted skills from their most recent resume
    latest_resume = db.execute("SELECT id FROM resumes WHERE user_id = ? ORDER BY upload_date DESC LIMIT 1", (user_id,)).fetchone()
    
    user_skills = []
    if latest_resume:
        user_skills_rows = db.execute("SELECT skill_name FROM extracted_skills WHERE resume_id = ?", (latest_resume['id'],)).fetchall()
        user_skills = [s['skill_name'].lower() for s in user_skills_rows]
        
    # Compare
    matched_skills = []
    missing_skills = []
    
    for req_skill in required_skills:
        # Simple string match for this week
        if req_skill in user_skills:
            matched_skills.append(req_skill.title())
        else:
            missing_skills.append(req_skill.title())
            
    # Find "related/extra" skills the user has that aren't specifically required
    extra_skills = [s.title() for s in user_skills if s not in required_skills]
    
    match_percentage = 0
    if required_skills:
        match_percentage = int((len(matched_skills) / len(required_skills)) * 100)
        
    return {
        'status': 'success',
        'target_role': target_role,
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'extra_skills': extra_skills,
        'match_percentage': match_percentage,
        'total_required': len(required_skills)
    }
