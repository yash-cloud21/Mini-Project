from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from forms.resume_forms import ResumeUploadForm
from services.resume_service import process_resume, get_user_resumes, get_resume_details

resume_bp = Blueprint('resume', __name__, url_prefix='/resume')

@resume_bp.route('/')
@login_required
def dashboard():
    resumes = get_user_resumes(current_user.id)
    return render_template('resume/dashboard.html', resumes=resumes)

@resume_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = ResumeUploadForm()
    if form.validate_on_submit():
        file = form.resume_file.data
        try:
            resume_id = process_resume(current_user.id, file, current_app.config['UPLOAD_FOLDER'])
            flash('Resume uploaded and analyzed successfully!', 'success')
            return redirect(url_for('resume.view', resume_id=resume_id))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('An unexpected error occurred while processing the resume.', 'danger')
            print(f"Resume processing error: {e}")
            
    return render_template('resume/upload.html', form=form)

@resume_bp.route('/view/<int:resume_id>')
@login_required
def view(resume_id):
    resume = get_resume_details(resume_id, current_user.id)
    if not resume:
        flash('Resume not found or you do not have permission to view it.', 'danger')
        return redirect(url_for('resume.dashboard'))
        
    return render_template('resume/view.html', resume=resume)
