from flask_login import LoginManager, UserMixin

# Single LoginManager instance used by the app
login_manager = LoginManager()


# ---- Fake user store (your dict-based system) ----
# Replace this with your config or real dict
USERS = {
    "admin": {
        "password": "admin123",
    },
    "test": {
        "password": "test",
    }
}


# ---- User object ----
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

    @property
    def username(self):
        return self.id


# ---- Flask-Login required callback ----
@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login calls this to reload the user from the session.
    Since we only use a dict, we just check if the user exists.
    """
    if user_id in USERS:
        return User(user_id)
    return None


# ---- Authentication helpers ----
def authenticate(username, password):
    """
    Checks credentials against the USERS dict.
    Returns User object if valid, otherwise None.
    """
    user = USERS.get(username)
    if not user:
        return None

    if user["password"] != password:
        return None

    return User(username)

def get_user_data(user):
    return {"profilePicture": "https://stager-prod.s3.eu-west-1.amazonaws.com/images/74/Accounts/3038433/profile-picture-1769098720?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20260703T092043Z&X-Amz-SignedHeaders=host&X-Amz-Expires=484756&X-Amz-Credential=AKIA46KEPVSAZU4VAMAM%2F20260703%2Feu-west-1%2Fs3%2Faws4_request&X-Amz-Signature=4de9fb54e1868adea6db4cb62f0b9455b0a20889513ed3d66a3063ca939547ec"}