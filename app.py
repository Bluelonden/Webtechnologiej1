from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from forms import LoginForm, RegistrationForm
from models import db, migrate, login_manager, User, Movie
from dotenv import load_dotenv
import requests
import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'videotheek.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TMDB_API_KEY'] = os.getenv('TMDB_API_KEY')

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
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user) 
            flash('Welkom terug! Je bent nu ingelogd.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Ongeldige gebruikersnaam of wachtwoord.', 'danger')
            
    return render_template("login.html", form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # checkt of username of email al bestaan
        check_user = User.query.filter_by(username=form.username.data).first()
        check_email = User.query.filter_by(email=form.email.data).first()

        if check_user:
            flash("Deze gebruikersnaam is al bezet!", "danger")
            return render_template("register.html", form=form)
        
        if check_email:
            flash("Dit e-mailadres is al in gebruik!", "danger")
            return render_template("register.html", form=form)

        # als alles oke is, opslaan
        new_user = User(
            email=form.email.data,
            username=form.username.data,
            password=form.password.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Account succesvol aangemaakt!", "success")
        return redirect(url_for('login'))
        
    return render_template("register.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Je bent nu uitgelogd.', 'info')
    return redirect(url_for('home'))

@app.route("/genre/horror")
@login_required
def horror():
    api_key = app.config['TMDB_API_KEY']
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&with_genres=27&language=nl-NL"
    
    response = requests.get(url)
    movies = response.json().get('results', [])[:8]

    reserved_ids = [m.tmdb_id for m in Movie.query.filter_by(is_reserved=True).all()]
    my_reserved_ids = [m.tmdb_id for m in Movie.query.filter_by(is_reserved=True, reserved_by=current_user.id).all()]

    return render_template('horror.html', movies=movies, reserved_ids=reserved_ids, my_reserved_ids=my_reserved_ids)

@app.route("/genre/<string:genre_naam>")
@login_required
def toon_genre(genre_naam):
    api_key = app.config['TMDB_API_KEY']
    
    # Koppel de naam uit de URL aan het juiste TMDB ID
    genre_ids = {
        'horror': 27,
        'comedy': 35,
        'drama': 18,
        'actie': 28
    }
    
    # zoek het ID op, of geef een 404 als het genre niet bestaat
    genre_id = genre_ids.get(genre_naam.lower())
    if not genre_id:
        return "Genre niet gevonden", 404
    
    # TMDB Request
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&with_genres={genre_id}&language=nl-NL"
    movies = requests.get(url).json().get('results', [])[:8]

    # database checks
    reserved_ids = [m.tmdb_id for m in Movie.query.filter_by(is_reserved=True).all()]
    my_reserved_ids = [m.tmdb_id for m in Movie.query.filter_by(is_reserved=True, reserved_by=current_user.id).all()]

    #wwe sturen de gebruiker naar de specifieke html voor dat genre
    return render_template(f'{genre_naam.lower()}.html', 
                           movies=movies, 
                           reserved_ids=reserved_ids, 
                           my_reserved_ids=my_reserved_ids)

@app.route("/mijn_reserveringen")
@login_required
def mijn_reserveringen():
    # Haal alle films op die door de huidige gebruiker zijn gereserveerd
    reserveringen = Movie.query.filter_by(is_reserved=True, reserved_by=current_user.id).all()
    return render_template('mijn_reserveringen.html', reserveringen=reserveringen)

@app.route("/film/<int:movie_id>")
def film_detail(movie_id):
    api_key = app.config['TMDB_API_KEY']
    
    # haal film details op
    movie = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=nl-NL").json()
    
    # haal Watch Providers op
    providers_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={api_key}"
    providers_data = requests.get(providers_url).json()
    
    # Pak de Nederlandse resultaten
    results_nl = providers_data.get('results', {}).get('NL', {})
    
    streaming = results_nl.get('flatrate', [])
    koop = results_nl.get('buy', [])

    # DEBUG: Check je terminal om te zien of er iets gevonden is
    print(f"DEBUG: Providers gevonden voor {movie.get('title')}: {len(streaming)} streaming, {len(koop)} koop")
    
    return render_template('film_detail.html', movie=movie, streaming=streaming, koop=koop)

@app.route("/reserveer/<int:tmdb_id>/<string:title>")
@login_required
def reserveer(tmdb_id, title):
    # check of de film al in onze database staat
    movie = Movie.query.filter_by(tmdb_id=tmdb_id).first()

    if movie and movie.is_reserved:
        # de film is al bezet
        flash(f"Helaas, '{title}' is al gereserveerd door iemand anders.", "danger")
    else:
        if not movie:
            # Film bestaat nog niet in onze db, maak hem aan
            movie = Movie(tmdb_id=tmdb_id, title=title)
            db.session.add(movie)
        
        # zet de film op gereserveerd voor de huidige gebruiker
        movie.is_reserved = True
        movie.reserved_by = current_user.id
        db.session.commit()
        flash(f"Je hebt '{title}' succesvol gereserveerd!", "success")

    return redirect(request.referrer or url_for('home'))

@app.route("/annuleer/<int:tmdb_id>")
@login_required
def annuleer_reservering(tmdb_id):
    movie = Movie.query.filter_by(tmdb_id=tmdb_id).first()
    
    # check of de film bestaat en of de huidige gebruiker wel de eigenaar is
    if movie and movie.reserved_by == current_user.id:
        movie.is_reserved = False
        movie.reserved_by = None
        db.session.commit()
        flash("Reservering succesvol geannuleerd.", "info")
    else:
        flash("Je kunt deze reservering niet annuleren.", "danger")
        
    return redirect(request.referrer or url_for('home'))

with app.app_context():
    db.create_all()
    print("database en tabellen zijn gecontroleerd/aangemaakt")

if __name__ == '__main__':
    app.run(debug=True)