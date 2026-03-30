from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager
from sqlalchemy.orm import Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String
from flask_migrate import Migrate

# initialisatie van de database- en login-extensies
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# vertelt Flask-Login hoe een gebruiker opgehaald moet worden op basis van de ID in de sessie
@login_manager.user_loader
def load_user(user_id: int):
    return db.session.get(User, int(user_id))

class User(db.Model, UserMixin):
    """
    De User-klasse representeert zowel de database-tabel als het 
    gebruikersobject voor authenticatie.
    """
    __tablename__ = 'users'

    # database velden met constraints voor unieke waarden en sneller zoeken (index)
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    
    # we slaan nooit het echte wachtwoord op alleen een veilige hash
    password_hash: Mapped[str | None] = mapped_column(String(128))

    def __init__(self, email: str, username: str, password: str): 
        self.email = email
        self.username = username
        # Bij het aanmaken wordt het wachtwoord direct gehasht
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Controleert of een ingevoerd wachtwoord overeenkomt met de opgeslagen hash."""
        return check_password_hash(self.password_hash, password)