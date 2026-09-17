"""
Authentication routes — register, login, logout, profile.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from database.db import get_db
from models.user import User
from forms.auth_forms import RegistrationForm, LoginForm, ProfileForm

auth_bp = Blueprint('auth', __name__)


# ------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            role='student',
        )
        if user:
            # Create a blank student profile row
            db = get_db()
            db.execute(
                'INSERT INTO student_profiles (user_id, full_name) VALUES (?, ?)',
                (user.id, form.username.data),
            )
            db.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registration failed. Username or email may already exist.', 'error')

    return render_template('auth/register.html', form=form)


# ------------------------------------------------------------------
# Login / Logout
# ------------------------------------------------------------------

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Logged in successfully!', 'success')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))


# ------------------------------------------------------------------
# Student Profile
# ------------------------------------------------------------------

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    profile_data = db.execute(
        'SELECT * FROM student_profiles WHERE user_id = ?',
        (current_user.id,),
    ).fetchone()

    form = ProfileForm()

    if form.validate_on_submit():
        semester_val = int(form.semester.data) if form.semester.data else None

        if profile_data:
            db.execute(
                '''UPDATE student_profiles
                   SET full_name = ?, enrollment_number = ?, department = ?,
                       semester = ?, phone = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE user_id = ?''',
                (form.full_name.data, form.enrollment_number.data,
                 form.department.data, semester_val, form.phone.data,
                 current_user.id),
            )
        else:
            db.execute(
                '''INSERT INTO student_profiles
                   (user_id, full_name, enrollment_number, department, semester, phone)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (current_user.id, form.full_name.data, form.enrollment_number.data,
                 form.department.data, semester_val, form.phone.data),
            )
        db.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

    # Pre-populate form on GET
    if profile_data and request.method == 'GET':
        form.full_name.data = profile_data['full_name'] or ''
        form.enrollment_number.data = profile_data['enrollment_number'] or ''
        form.department.data = profile_data['department'] or ''
        form.semester.data = str(profile_data['semester']) if profile_data['semester'] else ''
        form.phone.data = profile_data['phone'] or ''

    return render_template('profile/profile.html', form=form, profile=profile_data)
