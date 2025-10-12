from sqlalchemy.orm import Session
from app.models.user import User, UserCreate, UserInDB, UserUpdate, UserRole
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.db.models import UserModel, UserRoleEnum

class UserService:
    @staticmethod
    def initialize_super_admin(db: Session):
        existing_user = UserRepository.get_by_username(db, settings.SUPER_ADMIN_USERNAME)

        if not existing_user:
            hashed_password = get_password_hash(settings.SUPER_ADMIN_PASSWORD)
            UserRepository.create(
                db=db,
                username=settings.SUPER_ADMIN_USERNAME,
                email=settings.SUPER_ADMIN_EMAIL,
                full_name=settings.SUPER_ADMIN_FULL_NAME,
                hashed_password=hashed_password,
                role=UserRoleEnum.ADMIN,
                disabled=False
            )

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> UserInDB | None:
        user_model = UserRepository.get_by_username(db, username)
        if user_model:
            return UserInDB(
                username=user_model.username,
                email=user_model.email,
                full_name=user_model.full_name,
                role=UserRole(user_model.role.value),
                disabled=user_model.disabled,
                hashed_password=user_model.hashed_password
            )
        return None

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> UserInDB | None:
        user_model = UserRepository.get_by_email(db, email)
        if user_model:
            return UserInDB(
                username=user_model.username,
                email=user_model.email,
                full_name=user_model.full_name,
                role=UserRole(user_model.role.value),
                disabled=user_model.disabled,
                hashed_password=user_model.hashed_password
            )
        return None

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        hashed_password = get_password_hash(user_data.password)

        role_enum = UserRoleEnum.ADMIN if user_data.role == UserRole.ADMIN else UserRoleEnum.EMPLOYEE

        user_model = UserRepository.create(
            db=db,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=role_enum,
            disabled=False
        )

        return User(
            username=user_model.username,
            email=user_model.email,
            full_name=user_model.full_name,
            role=UserRole(user_model.role.value),
            disabled=user_model.disabled
        )

    @staticmethod
    def update_user(db: Session, username: str, user_update: UserUpdate) -> User | None:
        update_dict = {}
        if user_update.email is not None:
            update_dict["email"] = user_update.email
        if user_update.full_name is not None:
            update_dict["full_name"] = user_update.full_name

        if not update_dict:
            return UserService.get_user_by_username(db, username)

        user_model = UserRepository.update(db, username, **update_dict)

        if user_model:
            return User(
                username=user_model.username,
                email=user_model.email,
                full_name=user_model.full_name,
                role=UserRole(user_model.role.value),
                disabled=user_model.disabled
            )
        return None

    @staticmethod
    def change_password(db: Session, username: str, new_password: str) -> bool:
        hashed_password = get_password_hash(new_password)
        user_model = UserRepository.update(db, username, hashed_password=hashed_password)
        return user_model is not None

    @staticmethod
    def disable_user(db: Session, username: str) -> User | None:
        user_model = UserRepository.update(db, username, disabled=True)
        if user_model:
            return User(
                username=user_model.username,
                email=user_model.email,
                full_name=user_model.full_name,
                role=UserRole(user_model.role.value),
                disabled=user_model.disabled
            )
        return None

    @staticmethod
    def enable_user(db: Session, username: str) -> User | None:
        user_model = UserRepository.update(db, username, disabled=False)
        if user_model:
            return User(
                username=user_model.username,
                email=user_model.email,
                full_name=user_model.full_name,
                role=UserRole(user_model.role.value),
                disabled=user_model.disabled
            )
        return None

    @staticmethod
    def change_user_role(db: Session, username: str, new_role: UserRole) -> User | None:
        role_enum = UserRoleEnum.ADMIN if new_role == UserRole.ADMIN else UserRoleEnum.EMPLOYEE
        user_model = UserRepository.update(db, username, role=role_enum)
        if user_model:
            return User(
                username=user_model.username,
                email=user_model.email,
                full_name=user_model.full_name,
                role=UserRole(user_model.role.value),
                disabled=user_model.disabled
            )
        return None

    @staticmethod
    def delete_user(db: Session, username: str) -> bool:
        return UserRepository.delete(db, username)

    @staticmethod
    def get_all_users(db: Session) -> list[User]:
        user_models = UserRepository.get_all(db)
        return [
            User(
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=UserRole(user.role.value),
                disabled=user.disabled
            )
            for user in user_models
        ]

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> UserInDB | None:
        user = UserService.get_user_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
