from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True, nullable=False)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Relatie toevoegen zodat SQLAlchemy sneller begrijpt hoe ze verbonden zijn
    reserved_movies = db.relationship('Movie', backref='user', lazy=True)

    def __init__(self, email, username, password): 
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Movie(db.Model):
    __tablename__ = 'movies'

    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    is_reserved = db.Column(db.Boolean, default=False)
    reserved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def __init__(self, tmdb_id, title, is_reserved=False, reserved_by=None):
        self.tmdb_id = tmdb_id
        self.title = title
        self.is_reserved = is_reserved
        self.reserved_by = reserved_by