"""
Academic module forms (Flask-WTF).

Subject choices for SelectFields are populated dynamically in the
route handlers (not here) because they require a database query.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, FloatField, SelectField,
    TextAreaField, DateField, SubmitField,
)
from wtforms.validators import DataRequired, NumberRange, Length, Optional


class SubjectForm(FlaskForm):
    """Admin form for adding a subject."""
    name = StringField('Subject Name', validators=[DataRequired(), Length(max=100)])
    code = StringField('Subject Code', validators=[DataRequired(), Length(max=20)])
    credits = IntegerField('Credits', validators=[DataRequired(), NumberRange(min=1, max=10)])
    semester = IntegerField('Semester', validators=[DataRequired(), NumberRange(min=1, max=8)])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Add Subject')


class MarksForm(FlaskForm):
    """Student form for recording exam marks."""
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    exam_type = SelectField('Exam Type', choices=[
        ('internal', 'Internal'),
        ('midterm', 'Midterm'),
        ('final', 'Final'),
        ('quiz', 'Quiz'),
        ('practical', 'Practical'),
    ], validators=[DataRequired()])
    marks_obtained = FloatField('Marks Obtained', validators=[DataRequired(), NumberRange(min=0)])
    max_marks = FloatField('Maximum Marks', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add Marks')


class AttendanceForm(FlaskForm):
    """Student form for recording daily attendance."""
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ], validators=[DataRequired()])
    submit = SubmitField('Record Attendance')


class AssignmentForm(FlaskForm):
    """Student form for adding assignments to track."""
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    due_date = DateField('Due Date', validators=[Optional()])
    submit = SubmitField('Add Assignment')
