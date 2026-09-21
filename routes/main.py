"""
Main / general routes — home page and authenticated dashboard.
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    """Public landing page.  Authenticated users go straight to dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('home.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Unified Dashboard — shows stats from Academics, Coding, Resume, and Career."""
    from services.academic_service import get_academic_summary
    from services.coding_service import get_coding_summary
    from services.resume_service import get_user_resumes, get_resume_details
    from services.career_service import analyze_skill_gap

    # 1. Academics
    acad_summary = get_academic_summary(current_user.id)
    
    # 2. Coding
    coding_summary = get_coding_summary(current_user.id)
    
    # 3. Resume
    resumes = get_user_resumes(current_user.id)
    resume_details = None
    if resumes:
        # Get latest resume details
        resume_details = get_resume_details(resumes[0]['id'], current_user.id)
        
    # 4. Career Match
    career_match = analyze_skill_gap(current_user.id)
    
    return render_template(
        'dashboard.html', 
        acad_summary=acad_summary,
        coding_summary=coding_summary,
        resume_details=resume_details,
        career_match=career_match
    )
