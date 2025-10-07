from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import ClientBiometricModel, BiometricTypeEnum
from typing import Optional, List
from uuid import UUID

class BiometricRepository:
    @staticmethod
    def create(db: Session, client_id: UUID, biometric_type: BiometricTypeEnum,
               compressed_data: str, thumbnail: Optional[str] = None,
               embedding: Optional[str] = None, meta_info: dict = None) -> ClientBiometricModel:
        """
        Create a new biometric record in the database.
        """
        db_biometric = ClientBiometricModel(
            client_id=client_id,
            type=biometric_type,
            compressed_data=compressed_data,
            thumbnail=thumbnail,
            embedding=embedding,
            is_active=True,
            meta_info=meta_info or {}
        )
        db.add(db_biometric)
        db.commit()
        db.refresh(db_biometric)
        return db_biometric

    @staticmethod
    def get_by_id(db: Session, biometric_id: UUID) -> Optional[ClientBiometricModel]:
        """
        Get biometric by ID.
        """
        return db.query(ClientBiometricModel).filter(ClientBiometricModel.id == biometric_id).first()

    @staticmethod
    def get_by_client_id(db: Session, client_id: UUID,
                        is_active: Optional[bool] = None) -> List[ClientBiometricModel]:
        """
        Get all biometric records for a specific client.
        """
        query = db.query(ClientBiometricModel).filter(ClientBiometricModel.client_id == client_id)

        if is_active is not None:
            query = query.filter(ClientBiometricModel.is_active == is_active)

        return query.all()

    @staticmethod
    def get_by_type(db: Session, biometric_type: BiometricTypeEnum,
                   is_active: bool = True) -> List[ClientBiometricModel]:
        """
        Get all biometric records of a specific type.
        """
        return db.query(ClientBiometricModel).filter(
            ClientBiometricModel.type == biometric_type,
            ClientBiometricModel.is_active == is_active
        ).all()

    @staticmethod
    def get_all(db: Session, is_active: Optional[bool] = None,
                limit: int = 1000, offset: int = 0) -> List[ClientBiometricModel]:
        """
        Get all biometric records with optional filtering.
        """
        query = db.query(ClientBiometricModel)

        if is_active is not None:
            query = query.filter(ClientBiometricModel.is_active == is_active)

        query = query.order_by(ClientBiometricModel.created_at.desc()).offset(offset).limit(limit)
        return query.all()

    @staticmethod
    def update(db: Session, biometric_id: UUID, **kwargs) -> Optional[ClientBiometricModel]:
        """
        Update biometric by ID.
        """
        biometric = db.query(ClientBiometricModel).filter(
            ClientBiometricModel.id == biometric_id
        ).first()
        if not biometric:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(biometric, key):
                setattr(biometric, key, value)

        db.commit()
        db.refresh(biometric)
        return biometric

    @staticmethod
    def delete(db: Session, biometric_id: UUID) -> bool:
        """
        Soft delete biometric by setting is_active to False.
        """
        biometric = db.query(ClientBiometricModel).filter(
            ClientBiometricModel.id == biometric_id
        ).first()
        if not biometric:
            return False

        biometric.is_active = False
        db.commit()
        return True

    @staticmethod
    async def create_async(db: AsyncSession, client_id: UUID,
                          biometric_type: BiometricTypeEnum, compressed_data: str,
                          thumbnail: Optional[str] = None, embedding: Optional[str] = None,
                          meta_info: dict = None) -> ClientBiometricModel:
        """
        Create a new biometric record in the database (async).
        """
        db_biometric = ClientBiometricModel(
            client_id=client_id,
            type=biometric_type,
            compressed_data=compressed_data,
            thumbnail=thumbnail,
            embedding=embedding,
            is_active=True,
            meta_info=meta_info or {}
        )
        db.add(db_biometric)
        await db.commit()
        await db.refresh(db_biometric)
        return db_biometric

    @staticmethod
    async def get_by_id_async(db: AsyncSession, biometric_id: UUID) -> Optional[ClientBiometricModel]:
        """
        Get biometric by ID (async).
        """
        result = await db.execute(
            select(ClientBiometricModel).filter(ClientBiometricModel.id == biometric_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_client_id_async(db: AsyncSession, client_id: UUID,
                                    is_active: Optional[bool] = None) -> List[ClientBiometricModel]:
        """
        Get all biometric records for a specific client (async).
        """
        query = select(ClientBiometricModel).filter(ClientBiometricModel.client_id == client_id)

        if is_active is not None:
            query = query.filter(ClientBiometricModel.is_active == is_active)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_type_async(db: AsyncSession, biometric_type: BiometricTypeEnum,
                               is_active: bool = True) -> List[ClientBiometricModel]:
        """
        Get all biometric records of a specific type (async).
        """
        query = select(ClientBiometricModel).filter(
            ClientBiometricModel.type == biometric_type,
            ClientBiometricModel.is_active == is_active
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_all_async(db: AsyncSession, is_active: Optional[bool] = None,
                           limit: int = 1000, offset: int = 0) -> List[ClientBiometricModel]:
        """
        Get all biometric records with optional filtering (async).
        """
        query = select(ClientBiometricModel)

        if is_active is not None:
            query = query.filter(ClientBiometricModel.is_active == is_active)

        query = query.order_by(ClientBiometricModel.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_async(db: AsyncSession, biometric_id: UUID,
                          **kwargs) -> Optional[ClientBiometricModel]:
        """
        Update biometric by ID (async).
        """
        result = await db.execute(
            select(ClientBiometricModel).filter(ClientBiometricModel.id == biometric_id)
        )
        biometric = result.scalar_one_or_none()

        if not biometric:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(biometric, key):
                setattr(biometric, key, value)

        await db.commit()
        await db.refresh(biometric)
        return biometric

    @staticmethod
    async def delete_async(db: AsyncSession, biometric_id: UUID) -> bool:
        """
        Soft delete biometric by setting is_active to False (async).
        """
        result = await db.execute(
            select(ClientBiometricModel).filter(ClientBiometricModel.id == biometric_id)
        )
        biometric = result.scalar_one_or_none()

        if not biometric:
            return False

        biometric.is_active = False
        await db.commit()
        return True
