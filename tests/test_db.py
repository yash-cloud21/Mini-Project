def test_academic_db_write_roundtrip(app):
    """Test that we can insert an academic subject and retrieve it successfully."""
    with app.app_context():
        from database.db import get_db
        db = get_db()
        
        # Insert User (needed for foreign key)
        db.execute(
            'INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)',
            (2, 'db_user', 'db@test.com', 'hash')
        )
        
        # Insert Subject
        db.execute(
            'INSERT INTO subjects (id, name, code, semester) VALUES (?, ?, ?, ?)',
            (10, 'Data Structures', 'CS101', 3)
        )
        
        # Insert Mark
        db.execute(
            'INSERT INTO marks (user_id, subject_id, exam_type, marks_obtained, max_marks) VALUES (?, ?, ?, ?, ?)',
            (2, 10, 'Midterm', 85, 100)
        )
        db.commit()
        
        # Retrieve Mark
        mark = db.execute(
            '''SELECT m.*, s.name as subject_name 
               FROM marks m JOIN subjects s ON m.subject_id = s.id 
               WHERE m.user_id = 2'''
        ).fetchone()
        
        assert mark is not None
        assert mark['subject_name'] == 'Data Structures'
        assert mark['exam_type'] == 'Midterm'
        assert mark['marks_obtained'] == 85
        assert mark['max_marks'] == 100
