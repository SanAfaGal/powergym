from app.models.user import User, UserCreate, UserInDB, UserUpdate, UserRole
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from app.core.database import get_supabase_client

class UserService:
    @staticmethod
    def initialize_super_admin():
        supabase = get_supabase_client()

        existing_user = supabase.table("users").select("*").eq("username", settings.SUPER_ADMIN_USERNAME).maybe_single().execute()

        if not existing_user or not existing_user.data:
            hashed_password = get_password_hash(settings.SUPER_ADMIN_PASSWORD)
            user_data = {
                "username": settings.SUPER_ADMIN_USERNAME,
                "full_name": settings.SUPER_ADMIN_FULL_NAME,
                "email": settings.SUPER_ADMIN_EMAIL,
                "role": "admin",
                "hashed_password": hashed_password,
                "disabled": False,
            }
            supabase.table("users").insert(user_data).execute()

    @staticmethod
    def get_user_by_username(username: str) -> UserInDB | None:
        supabase = get_supabase_client()
        response = supabase.table("users").select("*").eq("username", username).maybe_single().execute()
        if response and response.data:
            return UserInDB(**response.data)
        return None

    @staticmethod
    def get_user_by_email(email: str) -> UserInDB | None:
        supabase = get_supabase_client()
        response = supabase.table("users").select("*").eq("email", email).maybe_single().execute()
        if response and response.data:
            return UserInDB(**response.data)
        return None

    @staticmethod
    def create_user(user_data: UserCreate) -> User:
        supabase = get_supabase_client()
        hashed_password = get_password_hash(user_data.password)

        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "hashed_password": hashed_password,
            "disabled": False
        }

        response = supabase.table("users").insert(user_dict).execute()

        if response and response.data:
            return User(**{k: v for k, v in response.data[0].items() if k != "hashed_password"})
        return None

    @staticmethod
    def update_user(username: str, user_update: UserUpdate) -> User | None:
        supabase = get_supabase_client()

        update_dict = {}
        if user_update.email is not None:
            update_dict["email"] = user_update.email
        if user_update.full_name is not None:
            update_dict["full_name"] = user_update.full_name

        if not update_dict:
            return UserService.get_user_by_username(username)

        response = supabase.table("users").update(update_dict).eq("username", username).execute()

        if response and response.data:
            return User(**{k: v for k, v in response.data[0].items() if k != "hashed_password"})
        return None

    @staticmethod
    def change_password(username: str, new_password: str) -> bool:
        supabase = get_supabase_client()
        hashed_password = get_password_hash(new_password)
        response = supabase.table("users").update({"hashed_password": hashed_password}).eq("username", username).execute()
        return bool(response and response.data)

    @staticmethod
    def disable_user(username: str) -> User | None:
        supabase = get_supabase_client()
        response = supabase.table("users").update({"disabled": True}).eq("username", username).execute()
        if response and response.data:
            return User(**{k: v for k, v in response.data[0].items() if k != "hashed_password"})
        return None

    @staticmethod
    def enable_user(username: str) -> User | None:
        supabase = get_supabase_client()
        response = supabase.table("users").update({"disabled": False}).eq("username", username).execute()
        if response and response.data:
            return User(**{k: v for k, v in response.data[0].items() if k != "hashed_password"})
        return None

    @staticmethod
    def change_user_role(username: str, new_role: UserRole) -> User | None:
        supabase = get_supabase_client()
        response = supabase.table("users").update({"role": new_role}).eq("username", username).execute()
        if response and response.data:
            return User(**{k: v for k, v in response.data[0].items() if k != "hashed_password"})
        return None

    @staticmethod
    def delete_user(username: str) -> bool:
        supabase = get_supabase_client()
        response = supabase.table("users").delete().eq("username", username).execute()
        return bool(response and response.data)

    @staticmethod
    def get_all_users() -> list[User]:
        supabase = get_supabase_client()
        response = supabase.table("users").select("*").execute()
        if response and response.data:
            return [
                User(**{k: v for k, v in user_dict.items() if k != "hashed_password"})
                for user_dict in response.data
            ]
        return []

    @staticmethod
    def authenticate_user(username: str, password: str) -> UserInDB | None:
        user = UserService.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
