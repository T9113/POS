from pos_app.models.user_model import UserModel
from pos_app.models.activity_model import ActivityModel

class AuthController:
    _current_user = None

    @classmethod
    def login(cls, username: str, password: str) -> tuple[bool, str]:
        user = UserModel.authenticate(username, password)
        if not user:
            return False, "Invalid username or password"
        if not user.get("is_active"):
            return False, "User account has been deactivated"

        cls._current_user = user
        ActivityModel.log(user["id"], "LOGIN", f"User {user['username']} logged in successfully")
        return True, "Login successful"

    @classmethod
    def logout(cls):
        if cls._current_user:
            ActivityModel.log(cls._current_user["id"], "LOGOUT", f"User {cls._current_user['username']} logged out")
        cls._current_user = None

    @classmethod
    def get_current_user(cls) -> dict:
        return cls._current_user

    @classmethod
    def is_logged_in(cls) -> bool:
        return cls._current_user is not None

    @classmethod
    def is_admin(cls) -> bool:
        return cls._current_user is not None and cls._current_user.get("role") == "Admin"

    @classmethod
    def can_access(cls, screen_name: str) -> bool:
        """Cashiers can only access POS screen. Admins can access everything."""
        if cls.is_admin():
            return True
        # Cashier role restrictions
        allowed_cashier_screens = ["pos", "dashboard"]
        return screen_name.lower() in allowed_cashier_screens
