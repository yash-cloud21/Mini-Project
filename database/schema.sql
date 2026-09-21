-- ============================================================
-- Student Career Platform — Week 1 Schema
-- Tables: users, student_profiles, subjects, marks,
--         attendance, assignments
-- ============================================================

-- Core user accounts
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT    UNIQUE NOT NULL,
    email           TEXT    UNIQUE NOT NULL,
    password_hash   TEXT    NOT NULL,
    role            TEXT    NOT NULL DEFAULT 'student'
                            CHECK(role IN ('student', 'admin')),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Extended student profile information
CREATE TABLE IF NOT EXISTS student_profiles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER UNIQUE NOT NULL,
    full_name           TEXT,
    enrollment_number   TEXT    UNIQUE,
    department          TEXT,
    semester            INTEGER,
    phone               TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Subjects (created by admin, shared across students)
CREATE TABLE IF NOT EXISTS subjects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    code        TEXT    UNIQUE NOT NULL,
    credits     INTEGER DEFAULT 3,
    semester    INTEGER,
    department  TEXT,
    created_by  INTEGER,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Student marks per subject per exam
CREATE TABLE IF NOT EXISTS marks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    subject_id      INTEGER NOT NULL,
    exam_type       TEXT    NOT NULL
                            CHECK(exam_type IN ('internal','midterm','final','quiz','practical')),
    marks_obtained  REAL    NOT NULL,
    max_marks       REAL    NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- Daily attendance per subject
CREATE TABLE IF NOT EXISTS attendance (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    subject_id  INTEGER NOT NULL,
    date        DATE    NOT NULL,
    status      TEXT    NOT NULL
                        CHECK(status IN ('present','absent','late')),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    UNIQUE(user_id, subject_id, date)
);

-- Student assignments per subject
CREATE TABLE IF NOT EXISTS assignments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    subject_id      INTEGER NOT NULL,
    title           TEXT    NOT NULL,
    description     TEXT,
    due_date        DATE,
    status          TEXT    NOT NULL DEFAULT 'pending'
                            CHECK(status IN ('pending','completed','overdue')),
    submitted_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);


-- ============================================================
-- Week 2: Coding Practice Platform
-- ============================================================

-- Coding problems (seeded by admin / service)
CREATE TABLE IF NOT EXISTS coding_problems (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT    NOT NULL,
    topic           TEXT    NOT NULL,
    difficulty      TEXT    NOT NULL CHECK(difficulty IN ('easy','medium','hard')),
    description     TEXT    NOT NULL,
    input_format    TEXT,
    output_format   TEXT,
    examples        TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Test cases for each problem
CREATE TABLE IF NOT EXISTS test_cases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id      INTEGER NOT NULL,
    input_data      TEXT    NOT NULL,
    expected_output TEXT    NOT NULL,
    is_sample       INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (problem_id) REFERENCES coding_problems(id) ON DELETE CASCADE
);

-- Student code submissions
CREATE TABLE IF NOT EXISTS coding_submissions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    problem_id      INTEGER NOT NULL,
    code            TEXT    NOT NULL,
    language        TEXT    NOT NULL DEFAULT 'python',
    result          TEXT    NOT NULL
                            CHECK(result IN ('accepted','wrong_answer','error','timeout')),
    tests_passed    INTEGER DEFAULT 0,
    tests_total     INTEGER DEFAULT 0,
    result_detail   TEXT,
    submitted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)    REFERENCES users(id)           ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES coding_problems(id) ON DELETE CASCADE
);


-- ============================================================
-- Week 3: Resume Analyzer
-- ============================================================

-- Uploaded Resumes
CREATE TABLE IF NOT EXISTS resumes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    filename            TEXT    NOT NULL,
    original_filename   TEXT    NOT NULL,
    file_path           TEXT    NOT NULL,
    upload_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_text            TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Extracted Skills
CREATE TABLE IF NOT EXISTS extracted_skills (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id           INTEGER NOT NULL,
    skill_category      TEXT,
    skill_name          TEXT    NOT NULL,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
);

-- Extracted Education
CREATE TABLE IF NOT EXISTS extracted_education (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id           INTEGER NOT NULL,
    institution         TEXT,
    degree              TEXT,
    year                TEXT,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
);

-- Extracted Experience
CREATE TABLE IF NOT EXISTS extracted_experience (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id           INTEGER NOT NULL,
    company             TEXT,
    role                TEXT,
    duration            TEXT,
    description         TEXT,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
);

-- Extracted Projects
CREATE TABLE IF NOT EXISTS extracted_projects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id           INTEGER NOT NULL,
    title               TEXT,
    description         TEXT,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
);


-- ============================================================
-- Week 4: Career Skill Matching
-- ============================================================

-- Predefined Job Roles
CREATE TABLE IF NOT EXISTS job_roles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    title               TEXT    UNIQUE NOT NULL,
    description         TEXT
);

-- Required Skills for a Job Role
CREATE TABLE IF NOT EXISTS job_skills (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id             INTEGER NOT NULL,
    skill_name          TEXT    NOT NULL,
    is_core             INTEGER DEFAULT 1, -- 1 for required, 0 for nice-to-have
    FOREIGN KEY (role_id) REFERENCES job_roles(id) ON DELETE CASCADE
);

-- Student's Target Role
CREATE TABLE IF NOT EXISTS student_target_role (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER UNIQUE NOT NULL,
    role_id             INTEGER NOT NULL,
    selected_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES job_roles(id) ON DELETE CASCADE
);


-- ============================================================
-- Week 5: AI/NLP Insights Cache
-- ============================================================

CREATE TABLE IF NOT EXISTS ai_insights_cache (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    context_type        TEXT    NOT NULL, -- e.g., 'dashboard', 'resume'
    insight_text        TEXT    NOT NULL,
    source              TEXT    NOT NULL, -- 'ai' or 'fallback'
    generated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
