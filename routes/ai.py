from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from services.academic_service import get_academic_summary
from services.coding_service import get_coding_summary
from services.career_service import analyze_skill_gap
from services.resume_service import get_user_resumes, get_resume_details
from services.ai_service import generate_profile_insights, generate_resume_feedback

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

@ai_bp.route('/dashboard-insights')
@login_required
def dashboard_insights():
    """
    Returns AI generated personalized learning paths based on current user's aggregated data.
    """
    force_refresh = request.args.get('refresh', '0') == '1'
    
    # 1. Academics
    acad_summary = get_academic_summary(current_user.id)
    
    # 2. Coding
    coding_summary = get_coding_summary(current_user.id)
    
    # 3. Career Match
    career_match = analyze_skill_gap(current_user.id)
    
    result = generate_profile_insights(
        current_user.id, 
        acad_summary, 
        coding_summary, 
        career_match,
        force_refresh=force_refresh
    )
    
    return jsonify(result)

@ai_bp.route('/resume-feedback')
@login_required
def resume_feedback():
    """
    Returns AI generated resume improvement suggestions.
    """
    force_refresh = request.args.get('refresh', '0') == '1'
    
    # Get latest resume
    resumes = get_user_resumes(current_user.id)
    if not resumes:
        return jsonify({
            'source': 'fallback',
            'text': 'No resume uploaded yet. Please upload a resume to receive AI feedback.'
        })
        
    resume_id = resumes[0]['id']
    resume_details = get_resume_details(resume_id, current_user.id)
    raw_text = resume_details.raw_text if resume_details else ""
    
    # Get target role
    career_match = analyze_skill_gap(current_user.id)
    target_role_name = career_match.get('target_role', {}).get('title', 'General Software Engineering')
    
    if not raw_text:
        return jsonify({
            'source': 'fallback',
            'text': 'Could not extract text from your resume.'
        })
        
    result = generate_resume_feedback(
        current_user.id,
        raw_text,
        target_role_name,
        force_refresh=force_refresh
    )
    
    return jsonify(result)
