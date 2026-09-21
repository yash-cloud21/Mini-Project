from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from forms.career_forms import SelectRoleForm
from services.career_service import get_all_roles, set_target_role, get_target_role, analyze_skill_gap

career_bp = Blueprint('career', __name__, url_prefix='/career')

@career_bp.route('/select-role', methods=['GET', 'POST'])
@login_required
def select_role():
    form = SelectRoleForm()
    
    # Populate the choices
    roles = get_all_roles()
    form.role_id.choices = [(r['id'], r['title']) for r in roles]
    
    current_target = get_target_role(current_user.id)
    
    if request.method == 'GET' and current_target:
        form.role_id.data = current_target['id']
        
    if form.validate_on_submit():
        set_target_role(current_user.id, form.role_id.data)
        flash('Target role updated successfully.', 'success')
        return redirect(url_for('career.analysis'))
        
    return render_template('career/select.html', form=form, roles=roles, current_target=current_target)

@career_bp.route('/analysis')
@login_required
def analysis():
    gap_data = analyze_skill_gap(current_user.id)
    
    if gap_data['status'] == 'no_target_role':
        flash('Please select a target job role first.', 'info')
        return redirect(url_for('career.select_role'))
        
    return render_template('career/analysis.html', data=gap_data)
