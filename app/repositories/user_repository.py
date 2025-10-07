from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import UserModel, UserRoleEnum
from typing import Optional, List

class UserRepository:
    @staticmethod
    def create(db: Session, username: str, email: Optional[str], full_name: Optional[str],
               hashed_password: str, role: UserRoleEnum, disabled: bool = False) -> UserModel:
        """
        Create a new user in the database.
        """
        db_user = UserModel(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            disabled=disabled
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[UserModel]:
        """
        Get user by username.
        """
        return db.query(UserModel).filter(UserModel.username == username).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[UserModel]:
        """
        Get user by email.
        """
        return db.query(UserModel).filter(UserModel.email == email).first()

    @staticmethod
    def get_all(db: Session) -> List[UserModel]:
        """
        Get all users.
        """
        return db.query(UserModel).all()

    @staticmethod
    def update(db: Session, username: str, **kwargs) -> Optional[UserModel]:
        """
        Update user by username.
        """
        user = db.query(UserModel).filter(UserModel.username == username).first()
        if not user:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, username: str) -> bool:
        """
        Delete user by username.
        """
        user = db.query(UserModel).filter(UserModel.username == username).first()
        if not user:
            return False

        db.delete(user)
        db.commit()
        return True

    @staticmethod
    async def create_async(db: AsyncSession, username: str, email: Optional[str],
                          full_name: Optional[str], hashed_password: str,
                          role: UserRoleEnum, disabled: bool = False) -> UserModel:
        """
        Create a new user in the database (async).
        """
        db_user = UserModel(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            disabled=disabled
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def get_by_username_async(db: AsyncSession, username: str) -> Optional[UserModel]:
        """
        Get user by username (async).
        """
        result = await db.execute(select(UserModel).filter(UserModel.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email_async(db: AsyncSession, email: str) -> Optional[UserModel]:
        """
        Get user by email (async).
        """
        result = await db.execute(select(UserModel).filter(UserModel.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_async(db: AsyncSession) -> List[UserModel]:
        """
        Get all users (async).
        """
        result = await db.execute(select(UserModel))
        return result.scalars().all()

    @staticmethod
    async def update_async(db: AsyncSession, username: str, **kwargs) -> Optional[UserModel]:
        """
        Update user by username (async).
        """
        result = await db.execute(select(UserModel).filter(UserModel.username == username))
        user = result.scalar_one_or_none()

        if not user:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete_async(db: AsyncSession, username: str) -> bool:
        """
        Delete user by username (async).
        """
        result = await db.execute(select(UserModel).filter(UserModel.username == username))
        user = result.scalar_one_or_none()

        if not user:
            return False

        await db.delete(user)
        await db.commit()
        return True
