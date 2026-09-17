"""
Academic service — all metric calculations with transparent,
documented formulas.

Every function that computes a percentage shows its formula in the
docstring so the calculation is fully explainable to the user.
"""

from database.db import get_db


# ==================================================================
# Individual metric calculations
# ==================================================================

def calculate_marks_percentage(user_id, subject_id=None):
    """
    Marks Percentage
    ----------------
    Formula:  (Σ marks_obtained  /  Σ max_marks) × 100

    If subject_id is None → calculates across ALL subjects.
    Returns 0.0 when there is no data.
    """
    db = get_db()
    if subject_id:
        row = db.execute(
            'SELECT SUM(marks_obtained) AS total_obtained, SUM(max_marks) AS total_max '
            'FROM marks WHERE user_id = ? AND subject_id = ?',
            (user_id, subject_id),
        ).fetchone()
    else:
        row = db.execute(
            'SELECT SUM(marks_obtained) AS total_obtained, SUM(max_marks) AS total_max '
            'FROM marks WHERE user_id = ?',
            (user_id,),
        ).fetchone()

    if row and row['total_max'] and row['total_max'] > 0:
        return round((row['total_obtained'] / row['total_max']) * 100, 2)
    return 0.0


def calculate_attendance_percentage(user_id, subject_id=None):
    """
    Attendance Percentage
    ---------------------
    Formula:  (classes_present + classes_late) / total_classes × 100

    'Late' is counted as *attended* for percentage purposes.
    Returns 0.0 when there is no data.
    """
    db = get_db()
    if subject_id:
        total = db.execute(
            'SELECT COUNT(*) AS n FROM attendance WHERE user_id = ? AND subject_id = ?',
            (user_id, subject_id),
        ).fetchone()['n']
        attended = db.execute(
            "SELECT COUNT(*) AS n FROM attendance "
            "WHERE user_id = ? AND subject_id = ? AND status IN ('present', 'late')",
            (user_id, subject_id),
        ).fetchone()['n']
    else:
        total = db.execute(
            'SELECT COUNT(*) AS n FROM attendance WHERE user_id = ?',
            (user_id,),
        ).fetchone()['n']
        attended = db.execute(
            "SELECT COUNT(*) AS n FROM attendance "
            "WHERE user_id = ? AND status IN ('present', 'late')",
            (user_id,),
        ).fetchone()['n']

    if total > 0:
        return round((attended / total) * 100, 2)
    return 0.0


def calculate_assignment_completion(user_id, subject_id=None):
    """
    Assignment Completion Rate
    --------------------------
    Formula:  completed_assignments / total_assignments × 100

    Returns 0.0 when there is no data.
    """
    db = get_db()
    if subject_id:
        total = db.execute(
            'SELECT COUNT(*) AS n FROM assignments WHERE user_id = ? AND subject_id = ?',
            (user_id, subject_id),
        ).fetchone()['n']
        completed = db.execute(
            "SELECT COUNT(*) AS n FROM assignments "
            "WHERE user_id = ? AND subject_id = ? AND status = 'completed'",
            (user_id, subject_id),
        ).fetchone()['n']
    else:
        total = db.execute(
            'SELECT COUNT(*) AS n FROM assignments WHERE user_id = ?',
            (user_id,),
        ).fetchone()['n']
        completed = db.execute(
            "SELECT COUNT(*) AS n FROM assignments "
            "WHERE user_id = ? AND status = 'completed'",
            (user_id,),
        ).fetchone()['n']

    if total > 0:
        return round((completed / total) * 100, 2)
    return 0.0


# ==================================================================
# Comprehensive academic summary
# ==================================================================

def get_academic_summary(user_id):
    """
    Build a complete academic summary for the student dashboard.

    Overall Academic Score
    ---------------------
    Formula:
        (Marks%  × 0.50) + (Attendance%  × 0.30) + (Assignments%  × 0.20)

    Weight rationale:
        • Marks      50 %  — primary academic indicator
        • Attendance  30 %  — regularity and discipline
        • Assignments 20 %  — practical work completion
    """
    db = get_db()

    # Find every subject the student has *any* data for
    subjects = db.execute(
        '''SELECT DISTINCT s.* FROM subjects s
           LEFT JOIN marks       m   ON s.id = m.subject_id   AND m.user_id   = ?
           LEFT JOIN attendance  a   ON s.id = a.subject_id   AND a.user_id   = ?
           LEFT JOIN assignments asn ON s.id = asn.subject_id AND asn.user_id = ?
           WHERE m.id IS NOT NULL OR a.id IS NOT NULL OR asn.id IS NOT NULL''',
        (user_id, user_id, user_id),
    ).fetchall()

    subject_summaries = []
    for subj in subjects:
        subject_summaries.append({
            'id': subj['id'],
            'name': subj['name'],
            'code': subj['code'],
            'credits': subj['credits'],
            'marks_percentage': calculate_marks_percentage(user_id, subj['id']),
            'attendance_percentage': calculate_attendance_percentage(user_id, subj['id']),
            'assignment_completion': calculate_assignment_completion(user_id, subj['id']),
        })

    # Overall (across all subjects)
    overall_marks = calculate_marks_percentage(user_id)
    overall_attendance = calculate_attendance_percentage(user_id)
    overall_assignments = calculate_assignment_completion(user_id)

    # Weighted overall score
    MARKS_WEIGHT = 0.50
    ATTENDANCE_WEIGHT = 0.30
    ASSIGNMENT_WEIGHT = 0.20

    overall_score = round(
        (overall_marks * MARKS_WEIGHT)
        + (overall_attendance * ATTENDANCE_WEIGHT)
        + (overall_assignments * ASSIGNMENT_WEIGHT),
        2,
    )

    return {
        'subjects': subject_summaries,
        'overall_marks': overall_marks,
        'overall_attendance': overall_attendance,
        'overall_assignments': overall_assignments,
        'overall_score': overall_score,
        'weights': {
            'marks': MARKS_WEIGHT,
            'attendance': ATTENDANCE_WEIGHT,
            'assignments': ASSIGNMENT_WEIGHT,
        },
        'total_subjects': len(subject_summaries),
    }
