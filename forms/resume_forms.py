from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

class ResumeUploadForm(FlaskForm):
    resume_file = FileField('Upload Resume (PDF)', validators=[
        FileRequired(message="Please select a file to upload."),
        FileAllowed(['pdf'], message="Only PDF files are allowed.")
    ])
    submit = SubmitField('Upload and Analyze')
