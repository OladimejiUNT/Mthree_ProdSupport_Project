"""Incident and comment forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class IncidentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=255)])
    description = TextAreaField('Description', validators=[Optional()])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    severity = SelectField(
        'Severity',
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        validators=[DataRequired()],
    )
    submit = SubmitField('Submit Incident')


class UpdateIncidentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=255)])
    description = TextAreaField('Description', validators=[Optional()])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    severity = SelectField(
        'Severity',
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        validators=[DataRequired()],
    )
    # Admin-only fields (shown/enforced only for admins)
    status = SelectField(
        'Status',
        choices=[
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
        ],
        validators=[DataRequired()],
    )
    assigned_to = SelectField('Assign To', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Changes')


class CommentForm(FlaskForm):
    comment = TextAreaField(
        'Comment',
        validators=[DataRequired(), Length(min=1, max=2000)],
    )
    submit = SubmitField('Post Comment')
