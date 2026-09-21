from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

class SelectRoleForm(FlaskForm):
    role_id = SelectField('Select Target Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Set Target Role')
