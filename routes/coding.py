"""
Coding platform routes — problem browsing, submission, results, dashboard.
"""

import json
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from database.db import get_db
from forms.coding_forms import CodeSubmissionForm, ProblemFilterForm
from services.coding_service import run_all_tests, get_coding_summary

coding_bp = Blueprint('coding', __name__, url_prefix='/coding')


# ------------------------------------------------------------------
# Coding Dashboard
# ------------------------------------------------------------------

@coding_bp.route('/')
@login_required
def dashboard():
    summary = get_coding_summary(current_user.id)
    return render_template('coding/dashboard.html', summary=summary)


# ------------------------------------------------------------------
# Problem List (with filters)
# ------------------------------------------------------------------

@coding_bp.route('/problems')
@login_required
def problems():
    db = get_db()

    # Get distinct topics for the filter dropdown
    topics = db.execute(
        'SELECT DISTINCT topic FROM coding_problems ORDER BY topic'
    ).fetchall()

    filter_form = ProblemFilterForm(request.args, meta={'csrf': False})
    filter_form.topic.choices = [('', 'All Topics')] + [(t['topic'], t['topic'].title()) for t in topics]

    # Build query with filters
    query = 'SELECT p.* FROM coding_problems p WHERE 1=1'
    params = []

    topic = request.args.get('topic', '')
    difficulty = request.args.get('difficulty', '')
    status = request.args.get('status', '')

    if topic:
        query += ' AND p.topic = ?'
        params.append(topic)
    if difficulty:
        query += ' AND p.difficulty = ?'
        params.append(difficulty)

    query += ' ORDER BY p.topic, CASE p.difficulty WHEN "easy" THEN 1 WHEN "medium" THEN 2 WHEN "hard" THEN 3 END, p.title'

    all_problems = db.execute(query, params).fetchall()

    # Get solved/attempted status for current user
    solved_ids = set()
    attempted_ids = set()

    solved_rows = db.execute(
        "SELECT DISTINCT problem_id FROM coding_submissions WHERE user_id = ? AND result = 'accepted'",
        (current_user.id,),
    ).fetchall()
    solved_ids = {r['problem_id'] for r in solved_rows}

    attempted_rows = db.execute(
        'SELECT DISTINCT problem_id FROM coding_submissions WHERE user_id = ?',
        (current_user.id,),
    ).fetchall()
    attempted_ids = {r['problem_id'] for r in attempted_rows}

    # Build enriched problem list
    problem_list = []
    for p in all_problems:
        pid = p['id']
        if pid in solved_ids:
            p_status = 'solved'
        elif pid in attempted_ids:
            p_status = 'attempted'
        else:
            p_status = 'unsolved'

        # Apply status filter
        if status and p_status != status:
            continue

        problem_list.append({
            'id': pid,
            'title': p['title'],
            'topic': p['topic'],
            'difficulty': p['difficulty'],
            'status': p_status,
        })

    return render_template(
        'coding/problems.html',
        problems=problem_list,
        filter_form=filter_form,
        total=len(problem_list),
    )


# ------------------------------------------------------------------
# Problem Detail + Code Submission
# ------------------------------------------------------------------

@coding_bp.route('/problems/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def problem_detail(problem_id):
    db = get_db()
    problem = db.execute('SELECT * FROM coding_problems WHERE id = ?', (problem_id,)).fetchone()

    if not problem:
        flash('Problem not found.', 'error')
        return redirect(url_for('coding.problems'))

    # Get sample test cases (visible to user)
    sample_cases = db.execute(
        'SELECT * FROM test_cases WHERE problem_id = ? AND is_sample = 1',
        (problem_id,),
    ).fetchall()

    # Total test case count
    total_tests = db.execute(
        'SELECT COUNT(*) AS n FROM test_cases WHERE problem_id = ?',
        (problem_id,),
    ).fetchone()['n']

    # Check if user already solved this
    is_solved = db.execute(
        "SELECT 1 FROM coding_submissions WHERE user_id = ? AND problem_id = ? AND result = 'accepted'",
        (current_user.id, problem_id),
    ).fetchone() is not None

    # Recent submissions by this user for this problem
    submissions = db.execute(
        '''SELECT * FROM coding_submissions
           WHERE user_id = ? AND problem_id = ?
           ORDER BY submitted_at DESC LIMIT 10''',
        (current_user.id, problem_id),
    ).fetchall()

    form = CodeSubmissionForm()

    if form.validate_on_submit():
        source_code = form.code.data

        # Run tests in subprocess (NOT inside Flask process)
        result = run_all_tests(source_code, problem_id)

        # Save submission
        db.execute(
            '''INSERT INTO coding_submissions
               (user_id, problem_id, code, language, result,
                tests_passed, tests_total, result_detail)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (current_user.id, problem_id, source_code, 'python',
             result['overall'], result['passed'], result['total'],
             json.dumps(result['results'])),
        )
        db.commit()

        if result['overall'] == 'accepted':
            flash('All test cases passed! Problem solved!', 'success')
        elif result['overall'] == 'timeout':
            flash('Time Limit Exceeded. Optimize your solution.', 'warning')
        elif result['overall'] == 'error':
            flash('Runtime Error. Check your code for errors.', 'error')
        else:
            flash(f"Wrong Answer. Passed {result['passed']}/{result['total']} test cases.", 'error')

        return redirect(url_for('coding.submission_result',
                                problem_id=problem_id,
                                submission_id=db.execute('SELECT last_insert_rowid()').fetchone()[0]))

    return render_template(
        'coding/problem_detail.html',
        problem=problem,
        sample_cases=sample_cases,
        total_tests=total_tests,
        is_solved=is_solved,
        submissions=submissions,
        form=form,
    )


# ------------------------------------------------------------------
# Submission Result
# ------------------------------------------------------------------

@coding_bp.route('/problems/<int:problem_id>/result/<int:submission_id>')
@login_required
def submission_result(problem_id, submission_id):
    db = get_db()

    submission = db.execute(
        '''SELECT s.*, p.title AS problem_title, p.difficulty
           FROM coding_submissions s
           JOIN coding_problems p ON s.problem_id = p.id
           WHERE s.id = ? AND s.user_id = ?''',
        (submission_id, current_user.id),
    ).fetchone()

    if not submission:
        flash('Submission not found.', 'error')
        return redirect(url_for('coding.problems'))

    # Parse result detail JSON
    result_detail = []
    if submission['result_detail']:
        try:
            result_detail = json.loads(submission['result_detail'])
        except json.JSONDecodeError:
            pass

    return render_template(
        'coding/submission_result.html',
        submission=submission,
        result_detail=result_detail,
        problem_id=problem_id,
    )


# ------------------------------------------------------------------
# Admin: Add Problem (basic — for admin to add more problems)
# ------------------------------------------------------------------

@coding_bp.route('/admin/problems', methods=['GET'])
@login_required
def admin_problems():
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('coding.dashboard'))

    db = get_db()
    all_problems = db.execute(
        '''SELECT p.*, COUNT(tc.id) AS test_count
           FROM coding_problems p
           LEFT JOIN test_cases tc ON p.id = tc.problem_id
           GROUP BY p.id
           ORDER BY p.topic, p.difficulty'''
    ).fetchall()

    return render_template('coding/admin_problems.html', problems=all_problems)
