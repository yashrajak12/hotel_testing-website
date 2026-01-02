from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db, login_manager

class Role(Enum):
    ADMIN = 'Admin'
    MANAGER = 'Manager'
    CHEF = 'Chef'
    WAITER = 'Waiter'
    CASHIER = 'Cashier'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # 255 safe hai scrypt ke liye
    role = db.Column(db.Enum(Role), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Flask-Login required methods
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))