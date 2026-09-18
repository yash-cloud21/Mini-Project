"""
Coding module forms (Flask-WTF).
"""

from flask_wtf import FlaskForm
from wtforms import (
    TextAreaField, SelectField, SubmitField, HiddenField,
)
from wtforms.validators import DataRequired, Optional


class CodeSubmissionForm(FlaskForm):
    """Form for submitting code to a problem."""
    code = TextAreaField('Your Code', validators=[DataRequired()])
    language = HiddenField('Language', default='python')
    submit = SubmitField('Submit Code')


class ProblemFilterForm(FlaskForm):
    """Filter controls for the problems list (no submit — filters via GET)."""
    topic = SelectField('Topic', choices=[('', 'All Topics')], validators=[Optional()])
    difficulty = SelectField('Difficulty', choices=[
        ('', 'All Difficulties'),
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ], validators=[Optional()])
    status = SelectField('Status', choices=[
        ('', 'All'),
        ('solved', 'Solved'),
        ('attempted', 'Attempted'),
        ('unsolved', 'Unsolved'),
    ], validators=[Optional()])
