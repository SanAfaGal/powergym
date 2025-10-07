from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.db.models import ClientModel, DocumentTypeEnum, GenderTypeEnum
from typing import Optional, List
from uuid import UUID
from datetime import date

class ClientRepository:
    @staticmethod
    def create(db: Session, dni_type: DocumentTypeEnum, dni_number: str, first_name: str,
               middle_name: Optional[str], last_name: str, second_last_name: Optional[str],
               phone: str, alternative_phone: Optional[str], birth_date: date,
               gender: GenderTypeEnum, address: Optional[str]) -> ClientModel:
        """
        Create a new client in the database.
        """
        db_client = ClientModel(
            dni_type=dni_type,
            dni_number=dni_number,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            second_last_name=second_last_name,
            phone=phone,
            alternative_phone=alternative_phone,
            birth_date=birth_date,
            gender=gender,
            address=address,
            is_active=True
        )
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client

    @staticmethod
    def get_by_id(db: Session, client_id: UUID) -> Optional[ClientModel]:
        """
        Get client by ID.
        """
        return db.query(ClientModel).filter(ClientModel.id == client_id).first()

    @staticmethod
    def get_by_dni(db: Session, dni_number: str) -> Optional[ClientModel]:
        """
        Get client by DNI number.
        """
        return db.query(ClientModel).filter(ClientModel.dni_number == dni_number).first()

    @staticmethod
    def get_all(db: Session, is_active: Optional[bool] = None, limit: int = 100,
                offset: int = 0) -> List[ClientModel]:
        """
        Get all clients with optional filtering.
        """
        query = db.query(ClientModel)

        if is_active is not None:
            query = query.filter(ClientModel.is_active == is_active)

        query = query.order_by(ClientModel.created_at.desc()).offset(offset).limit(limit)
        return query.all()

    @staticmethod
    def search(db: Session, search_term: str, limit: int = 50) -> List[ClientModel]:
        """
        Search clients by name, DNI, or phone.
        """
        search_pattern = f"%{search_term}%"
        return db.query(ClientModel).filter(
            or_(
                ClientModel.first_name.ilike(search_pattern),
                ClientModel.last_name.ilike(search_pattern),
                ClientModel.dni_number.ilike(search_pattern),
                ClientModel.phone.ilike(search_pattern)
            )
        ).limit(limit).all()

    @staticmethod
    def update(db: Session, client_id: UUID, **kwargs) -> Optional[ClientModel]:
        """
        Update client by ID.
        """
        client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
        if not client:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(client, key):
                setattr(client, key, value)

        db.commit()
        db.refresh(client)
        return client

    @staticmethod
    def delete(db: Session, client_id: UUID) -> bool:
        """
        Soft delete client by setting is_active to False.
        """
        client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
        if not client:
            return False

        client.is_active = False
        db.commit()
        return True

    @staticmethod
    async def create_async(db: AsyncSession, dni_type: DocumentTypeEnum, dni_number: str,
                          first_name: str, middle_name: Optional[str], last_name: str,
                          second_last_name: Optional[str], phone: str,
                          alternative_phone: Optional[str], birth_date: date,
                          gender: GenderTypeEnum, address: Optional[str]) -> ClientModel:
        """
        Create a new client in the database (async).
        """
        db_client = ClientModel(
            dni_type=dni_type,
            dni_number=dni_number,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            second_last_name=second_last_name,
            phone=phone,
            alternative_phone=alternative_phone,
            birth_date=birth_date,
            gender=gender,
            address=address,
            is_active=True
        )
        db.add(db_client)
        await db.commit()
        await db.refresh(db_client)
        return db_client

    @staticmethod
    async def get_by_id_async(db: AsyncSession, client_id: UUID) -> Optional[ClientModel]:
        """
        Get client by ID (async).
        """
        result = await db.execute(select(ClientModel).filter(ClientModel.id == client_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_dni_async(db: AsyncSession, dni_number: str) -> Optional[ClientModel]:
        """
        Get client by DNI number (async).
        """
        result = await db.execute(select(ClientModel).filter(ClientModel.dni_number == dni_number))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_async(db: AsyncSession, is_active: Optional[bool] = None,
                           limit: int = 100, offset: int = 0) -> List[ClientModel]:
        """
        Get all clients with optional filtering (async).
        """
        query = select(ClientModel)

        if is_active is not None:
            query = query.filter(ClientModel.is_active == is_active)

        query = query.order_by(ClientModel.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_async(db: AsyncSession, search_term: str, limit: int = 50) -> List[ClientModel]:
        """
        Search clients by name, DNI, or phone (async).
        """
        search_pattern = f"%{search_term}%"
        query = select(ClientModel).filter(
            or_(
                ClientModel.first_name.ilike(search_pattern),
                ClientModel.last_name.ilike(search_pattern),
                ClientModel.dni_number.ilike(search_pattern),
                ClientModel.phone.ilike(search_pattern)
            )
        ).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_async(db: AsyncSession, client_id: UUID, **kwargs) -> Optional[ClientModel]:
        """
        Update client by ID (async).
        """
        result = await db.execute(select(ClientModel).filter(ClientModel.id == client_id))
        client = result.scalar_one_or_none()

        if not client:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(client, key):
                setattr(client, key, value)

        await db.commit()
        await db.refresh(client)
        return client

    @staticmethod
    async def delete_async(db: AsyncSession, client_id: UUID) -> bool:
        """
        Soft delete client by setting is_active to False (async).
        """
        result = await db.execute(select(ClientModel).filter(ClientModel.id == client_id))
        client = result.scalar_one_or_none()

        if not client:
            return False

        client.is_active = False
        await db.commit()
        return True
