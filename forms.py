from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField(['Confirm Password'])
    validators=[DataRequired(), EqualTo('password')]
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])    
    password = PasswordField("Wachtwoord", render_kw={"Placeholder":"Wachtwoord"})
    submit = SubmitField("Inloggen", render_kw={"class":"btn btn-primary"})