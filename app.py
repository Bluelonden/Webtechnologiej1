from flask import Flask, render_template, session, redirect, url_for, flash
from flask_login import login_user
from forms import LoginForm, RegistrationForm
from models import db, migrate, User
import os

# bepaalt het pad van de map waar dit bestand in staat (handig voor de database-locatie)
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# configuratie: Geheime sleutel voor sessies en de koppeling met de SQLite database
app.config['SECRET_KEY'] = os.urandom(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'videotheek.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TMDB_API_KEY'] = '33ed5e054c689e5395354624ea39da89'

# koppel de database en migratie-tools aan de Flask-app
db.init_app(app)
migrate.init_app(app, db)

@app.route("/")
def home():
    """De landingspagina van de videotheek."""
    return render_template('main.html')

@app.route("/login", methods=['GET', 'POST']) 
def login():
    form = LoginForm()
    # controleert of het formulier is ingevuld en op de knop is gedrukt
    if form.validate_on_submit():
        # Zoek de gebruiker in de database op basis van de ingevoerde naam
        user = User.query.filter_by(username=form.username.data).first()
        
        # checkt of de gebruiker bestaat EN of het wachtwoord klopt via de hash
        if user is not None and user.check_password(form.password.data):
            login_user(user) # Onthoudt de gebruiker voor de rest van de sessie
            flash('Succesvol ingelogd!', 'success')
            return redirect(url_for('home'))
        else:
            # geef een waarschuwing bij een foutieve combinatie (veiligheidshalve vaag houden)
            flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
            
    return render_template("login.html", form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # voor nu printen we de actie alleen in de console (later database-opslag toevoegen)
        print(f"Account created for {form.email.data}!")
        return redirect(url_for('login')) 
        
    return render_template("register.html", form=form)

if __name__ == '__main__':
    # start de server in debug-modus (handig tijdens het ontwikkelen)
    app.run(debug=True)