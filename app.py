from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from forms import LoginForm, RegistrationForm
from models import db, migrate, login_manager, User, Movie
from dotenv import load_dotenv
import requests
import os

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'videotheek.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TMDB_API_KEY'] = os.getenv('TMDB_API_KEY')

db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
login_manager.login_view = 'login' # type: ignore

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
        check_user = User.query.filter_by(username=form.username.data).first()
        check_email = User.query.filter_by(email=form.email.data).first()

        if check_user:
            flash("Deze gebruikersnaam is al bezet!", "danger")
            return render_template("register.html", form=form)
        
        if check_email:
            flash("Dit e-mailadres is al in gebruik!", "danger")
            return render_template("register.html", form=form)

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

# --- CRUD: DELETE (D) voor de USER ---
@app.route("/verwijder_account", methods=['POST'])
@login_required
def verwijder_account():
    user = User.query.get(current_user.id)
    
    # Eerst alle reserveringen van deze gebruiker vrijmaken of verwijderen
    # Gebruik het ID direct van current_user
    Movie.query.filter_by(reserved_by=current_user.get_id()).delete()
    
    logout_user()
    db.session.delete(user)
    db.session.commit()
    
    flash("Je account en al je reserveringen zijn definitief verwijderd.", "success")
    return redirect(url_for('home'))

@app.route("/genre/<string:genre_naam>")
@login_required
def toon_genre(genre_naam):
    api_key = app.config['TMDB_API_KEY']
    
    genre_ids = {
        'horror': 27,
        'comedy': 35,
        'drama': 18,
        'actie': 28
    }
    
    genre_id = genre_ids.get(genre_naam.lower())
    if not genre_id:
        return "Genre niet gevonden", 404

    url = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&with_genres={genre_id}&language=nl-NL"
    movies = requests.get(url).json().get('results', [])[:8]

    reserved_ids = [m.tmdb_id for m in Movie.query.filter_by(is_reserved=True).all()]
    my_reserved_ids = [m.tmdb_id for m in Movie.query.filter_by(is_reserved=True, reserved_by=current_user.id).all()]

    return render_template(f'{genre_naam.lower()}.html', 
                           movies=movies, 
                           reserved_ids=reserved_ids, 
                           my_reserved_ids=my_reserved_ids)

@app.route("/film/<int:movie_id>")
def film_detail(movie_id):
    api_key = app.config['TMDB_API_KEY']
    movie = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=nl-NL").json()
    providers_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={api_key}"
    providers_data = requests.get(providers_url).json()
    results_nl = providers_data.get('results', {}).get('NL', {})
    
    streaming = results_nl.get('flatrate', [])
    huren = results_nl.get('rent', [])
    koop = results_nl.get('buy', [])
    
    return render_template('film_detail.html', movie=movie, streaming=streaming, huren=huren, koop=koop)

# --- CRUD: CREATE/UPDATE voor RESERVERINGEN ---
@app.route("/reserveer/<int:tmdb_id>/<string:title>")
@login_required
def reserveer(tmdb_id, title):
    movie = Movie.query.filter_by(tmdb_id=tmdb_id).first()

    if movie and movie.is_reserved:
        flash(f"Helaas, '{title}' is al gereserveerd door iemand anders.", "danger")
    else:
        if not movie:
            movie = Movie(tmdb_id=tmdb_id, title=title)
            db.session.add(movie)
        
        movie.is_reserved = True
        movie.reserved_by = current_user.id
        db.session.commit()
        flash(f"Je hebt '{title}' succesvol gereserveerd!", "success")

    return redirect(request.referrer or url_for('home'))

# --- CRUD: DELETE (D) voor RESERVERINGEN ---
@app.route("/verwijder_reservering/<int:tmdb_id>")
@login_required
def verwijder_reservering(tmdb_id):
    # We gebruiken hier een echte DELETE operatie om de leraar CRUD te tonen
    movie = Movie.query.filter_by(tmdb_id=tmdb_id, reserved_by=current_user.id).first()
    
    if movie:
        db.session.delete(movie)
        db.session.commit()
        flash("Reservering is definitief verwijderd.", "info")
    else:
        flash("Reservering niet gevonden of je hebt geen rechten.", "danger")
        
    return redirect(request.referrer or url_for('home'))

@app.route("/annuleer/<int:tmdb_id>")
@login_required
def annuleer_reservering(tmdb_id):
    return redirect(url_for('verwijder_reservering', tmdb_id=tmdb_id))

with app.app_context():
    db.create_all()
    print("database en tabellen zijn gecontroleerd/aangemaakt")

if __name__ == '__main__':
    app.run(debug=True)