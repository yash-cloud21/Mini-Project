"""
Authentication and profile forms (Flask-WTF).
Every form inherits FlaskForm, which injects CSRF protection automatically.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SelectField, SubmitField,
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Optional, ValidationError,
)

from database.db import get_db


# ------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------

class RegistrationForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=50)],
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()],
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6, message='Password must be at least 6 characters.')],
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')],
    )
    submit = SubmitField('Register')

    # Custom validators — WTForms calls validate_<field> automatically
    def validate_username(self, username):
        db = get_db()
        if db.execute('SELECT 1 FROM users WHERE username = ?', (username.data,)).fetchone():
            raise ValidationError('Username already taken.')

    def validate_email(self, email):
        db = get_db()
        if db.execute('SELECT 1 FROM users WHERE email = ?', (email.data,)).fetchone():
            raise ValidationError('Email already registered.')


# ------------------------------------------------------------------
# Login
# ------------------------------------------------------------------

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


# ------------------------------------------------------------------
# Student Profile
# ------------------------------------------------------------------

class ProfileForm(FlaskForm):
    full_name = StringField(
        'Full Name',
        validators=[DataRequired(), Length(max=100)],
    )
    enrollment_number = StringField(
        'Enrollment Number',
        validators=[Optional(), Length(max=50)],
    )
    department = StringField(
        'Department',
        validators=[Optional(), Length(max=100)],
    )
    semester = SelectField(
        'Semester',
        choices=[('', 'Select Semester')] + [(str(i), f'Semester {i}') for i in range(1, 9)],
        validators=[Optional()],
    )
    phone = StringField(
        'Phone',
        validators=[Optional(), Length(max=15)],
    )
    submit = SubmitField('Update Profile')
