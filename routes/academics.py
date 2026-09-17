"""
Academic module routes — subjects, marks, attendance, assignments, dashboard.
"""

import sqlite3
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from database.db import get_db
from forms.academic_forms import SubjectForm, MarksForm, AttendanceForm, AssignmentForm
from services.academic_service import get_academic_summary

academics_bp = Blueprint('academics', __name__, url_prefix='/academics')


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def admin_required(f):
    """Decorator that restricts a view to admin users only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def _subject_choices():
    """Return a list of (id, label) tuples for subject SelectFields."""
    db = get_db()
    rows = db.execute('SELECT id, name, code FROM subjects ORDER BY name').fetchall()
    return [(r['id'], f"{r['name']} ({r['code']})") for r in rows]


# ------------------------------------------------------------------
# Academic Dashboard
# ------------------------------------------------------------------

@academics_bp.route('/')
@login_required
def dashboard():
    summary = get_academic_summary(current_user.id)
    return render_template('academics/dashboard.html', summary=summary)


# ------------------------------------------------------------------
# Subjects
# ------------------------------------------------------------------

@academics_bp.route('/subjects')
@login_required
def subjects():
    db = get_db()
    all_subjects = db.execute(
        'SELECT * FROM subjects ORDER BY semester, name'
    ).fetchall()
    form = SubjectForm()
    return render_template('academics/subjects.html', subjects=all_subjects, form=form)


@academics_bp.route('/subjects/add', methods=['POST'])
@login_required
@admin_required
def add_subject():
    form = SubjectForm()
    if form.validate_on_submit():
        db = get_db()
        try:
            db.execute(
                '''INSERT INTO subjects (name, code, credits, semester, department, created_by)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (form.name.data, form.code.data.upper(), form.credits.data,
                 form.semester.data, form.department.data, current_user.id),
            )
            db.commit()
            flash(f'Subject "{form.name.data}" added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('A subject with that code already exists.', 'error')
        return redirect(url_for('academics.subjects'))

    # Validation failed — re-render subjects page with errors
    db = get_db()
    all_subjects = db.execute('SELECT * FROM subjects ORDER BY semester, name').fetchall()
    return render_template('academics/subjects.html', subjects=all_subjects, form=form)


@academics_bp.route('/subjects/<int:subject_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_subject(subject_id):
    db = get_db()
    db.execute('DELETE FROM subjects WHERE id = ?', (subject_id,))
    db.commit()
    flash('Subject deleted.', 'info')
    return redirect(url_for('academics.subjects'))


# ------------------------------------------------------------------
# Marks
# ------------------------------------------------------------------

@academics_bp.route('/marks', methods=['GET', 'POST'])
@login_required
def add_marks():
    form = MarksForm()
    form.subject_id.choices = _subject_choices()

    if form.validate_on_submit():
        if form.marks_obtained.data > form.max_marks.data:
            flash('Marks obtained cannot exceed maximum marks.', 'error')
        else:
            db = get_db()
            db.execute(
                '''INSERT INTO marks (user_id, subject_id, exam_type, marks_obtained, max_marks)
                   VALUES (?, ?, ?, ?, ?)''',
                (current_user.id, form.subject_id.data, form.exam_type.data,
                 form.marks_obtained.data, form.max_marks.data),
            )
            db.commit()
            flash('Marks added successfully!', 'success')
            return redirect(url_for('academics.add_marks'))

    db = get_db()
    marks = db.execute(
        '''SELECT m.*, s.name AS subject_name, s.code AS subject_code
           FROM marks m JOIN subjects s ON m.subject_id = s.id
           WHERE m.user_id = ?
           ORDER BY m.created_at DESC''',
        (current_user.id,),
    ).fetchall()

    return render_template('academics/add_marks.html', form=form, marks=marks)


@academics_bp.route('/marks/<int:mark_id>/delete', methods=['POST'])
@login_required
def delete_mark(mark_id):
    db = get_db()
    db.execute('DELETE FROM marks WHERE id = ? AND user_id = ?', (mark_id, current_user.id))
    db.commit()
    flash('Mark entry deleted.', 'info')
    return redirect(url_for('academics.add_marks'))


# ------------------------------------------------------------------
# Attendance
# ------------------------------------------------------------------

@academics_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
def record_attendance():
    form = AttendanceForm()
    form.subject_id.choices = _subject_choices()

    if form.validate_on_submit():
        db = get_db()
        try:
            db.execute(
                '''INSERT INTO attendance (user_id, subject_id, date, status)
                   VALUES (?, ?, ?, ?)''',
                (current_user.id, form.subject_id.data,
                 form.date.data, form.status.data),
            )
            db.commit()
            flash('Attendance recorded!', 'success')
            return redirect(url_for('academics.record_attendance'))
        except sqlite3.IntegrityError:
            flash('Attendance already recorded for this subject on this date.', 'error')

    db = get_db()
    attendance = db.execute(
        '''SELECT a.*, s.name AS subject_name, s.code AS subject_code
           FROM attendance a JOIN subjects s ON a.subject_id = s.id
           WHERE a.user_id = ?
           ORDER BY a.date DESC
           LIMIT 50''',
        (current_user.id,),
    ).fetchall()

    return render_template('academics/attendance.html', form=form, attendance=attendance)


@academics_bp.route('/attendance/<int:att_id>/delete', methods=['POST'])
@login_required
def delete_attendance(att_id):
    db = get_db()
    db.execute('DELETE FROM attendance WHERE id = ? AND user_id = ?', (att_id, current_user.id))
    db.commit()
    flash('Attendance record deleted.', 'info')
    return redirect(url_for('academics.record_attendance'))


# ------------------------------------------------------------------
# Assignments
# ------------------------------------------------------------------

@academics_bp.route('/assignments', methods=['GET', 'POST'])
@login_required
def assignments():
    form = AssignmentForm()
    form.subject_id.choices = _subject_choices()

    if form.validate_on_submit():
        db = get_db()
        db.execute(
            '''INSERT INTO assignments (user_id, subject_id, title, description, due_date)
               VALUES (?, ?, ?, ?, ?)''',
            (current_user.id, form.subject_id.data, form.title.data,
             form.description.data, form.due_date.data),
        )
        db.commit()
        flash('Assignment added!', 'success')
        return redirect(url_for('academics.assignments'))

    db = get_db()
    assignment_list = db.execute(
        '''SELECT a.*, s.name AS subject_name, s.code AS subject_code
           FROM assignments a JOIN subjects s ON a.subject_id = s.id
           WHERE a.user_id = ?
           ORDER BY
               CASE a.status WHEN 'pending' THEN 0 WHEN 'overdue' THEN 1 ELSE 2 END,
               a.due_date ASC''',
        (current_user.id,),
    ).fetchall()

    return render_template('academics/assignments.html', form=form, assignments=assignment_list)


@academics_bp.route('/assignments/<int:assignment_id>/complete', methods=['POST'])
@login_required
def complete_assignment(assignment_id):
    db = get_db()
    db.execute(
        '''UPDATE assignments
           SET status = 'completed', submitted_at = CURRENT_TIMESTAMP
           WHERE id = ? AND user_id = ?''',
        (assignment_id, current_user.id),
    )
    db.commit()
    flash('Assignment marked as completed!', 'success')
    return redirect(url_for('academics.assignments'))


@academics_bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    db = get_db()
    db.execute('DELETE FROM assignments WHERE id = ? AND user_id = ?', (assignment_id, current_user.id))
    db.commit()
    flash('Assignment deleted.', 'info')
    return redirect(url_for('academics.assignments'))
