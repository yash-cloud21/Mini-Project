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
    """Authenticated overview — shows quick stats and action links."""
    from services.academic_service import get_academic_summary
    summary = get_academic_summary(current_user.id)
    return render_template('dashboard.html', summary=summary)
