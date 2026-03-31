from flask import Flask, render_template, session, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from forms import LoginForm, RegistrationForm
from models import db, migrate, login_manager, User
import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Configuraties
app.config['SECRET_KEY'] = os.urandom(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'videotheek.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TMDB_API_KEY'] = '33ed5e054c689e5395354624ea39da89'

db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
login_manager.login_view = "login"

@app.route("/")
def home():
    """De landingspagina van de videotheek."""
    return render_template('main.html')

@app.route("/login", methods=['GET', 'POST']) 
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is not None and user.check_password(form.password.data):
            login_user(user) 
            flash('Succesvol ingelogd', 'success')
            return redirect(url_for('home'))
        else:
            flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
            
    return render_template("login.html", form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(
            email=form.email.data,
            username=form.username.data,
            password=form.password.data
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f"Account aangemaakt voor {form.username.data}! Je kunt nu inloggen.", "success")
        
        return redirect(url_for('login')) 
        
    return render_template("register.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Je bent nu uitgelogd.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)