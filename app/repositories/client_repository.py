from datetime import date
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    ClientModel, DocumentTypeEnum, GenderTypeEnum,
    SubscriptionModel, AttendanceModel
)


class ClientRepository:
    """
    Repository for managing Client database operations.

    This repository implements the Data Access Object pattern, providing
    a clean interface for CRUD operations and complex queries on ClientModel.
    Uses SQLAlchemy 2.0+ with the modern select() API.
    """

    @staticmethod
    def create(
            db: Session,
            dni_type: DocumentTypeEnum,
            dni_number: str,
            first_name: str,
            middle_name: Optional[str],
            last_name: str,
            second_last_name: Optional[str],
            phone: str,
            alternative_phone: Optional[str],
            birth_date: date,
            gender: GenderTypeEnum,
            address: Optional[str],
    ) -> ClientModel:
        """
        Create a new client in the database.

        Args:
            db: Database session.
            dni_type: Type of identification document.
            dni_number: Identification document number.
            first_name: Client's first name.
            middle_name: Client's middle name (optional).
            last_name: Client's last name.
            second_last_name: Client's second last name (optional).
            phone: Primary phone number.
            alternative_phone: Alternative phone number (optional).
            birth_date: Client's birthdate.
            gender: Client's gender.
            address: Client's address (optional).

        Returns:
            ClientModel: The newly created client instance.

        Raises:
            SQLAlchemyError: If database operation fails.
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
            is_active=True,
        )
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client

    @staticmethod
    def get_by_id(db: Session, client_id: UUID) -> Optional[ClientModel]:
        """
        Retrieve a client by their ID.

        Args:
            db: Database session.
            client_id: The UUID of the client to retrieve.

        Returns:
            ClientModel if found, None otherwise.
        """
        stmt = select(ClientModel).where(ClientModel.id == client_id)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_by_id_with_biometrics(db: Session, client_id: UUID) -> Optional[ClientModel]:
        """
        Retrieve a client by ID with eager loading of biometric data.

        Uses joined load to reduce N+1 queries when accessing biometrics.

        Args:
            db: Database session.
            client_id: The UUID of the client to retrieve.

        Returns:
            ClientModel with biometrics loaded, or None if not found.
        """
        stmt = (
            select(ClientModel)
            .options(joinedload(ClientModel.biometrics))
            .where(ClientModel.id == client_id)
        )
        return db.execute(stmt).scalars().unique().first()

    @staticmethod
    def get_by_dni(db: Session, dni_number: str) -> Optional[ClientModel]:
        """
        Retrieve a client by their DNI (identification number).

        Args:
            db: Database session.
            dni_number: The DNI number to search for.

        Returns:
            ClientModel if found, None otherwise.
        """
        stmt = select(ClientModel).where(ClientModel.dni_number == dni_number)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_all(
            db: Session,
            is_active: Optional[bool] = None,
            limit: int = 100,
            offset: int = 0,
    ) -> Sequence[ClientModel]:
        """
        Retrieve all clients with optional filtering and pagination.

        Args:
            db: Database session.
            is_active: Filter by active status (optional). If None, returns all.
            limit: Maximum number of clients to return (default: 100).
            offset: Number of clients to skip for pagination (default: 0).

        Returns:
            List of ClientModel instances, ordered by creation date (newest first).
        """
        stmt = select(ClientModel)

        if is_active is not None:
            stmt = stmt.where(ClientModel.is_active.is_(is_active))

        stmt = (
            stmt.order_by(ClientModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return db.execute(stmt).scalars().all()

    @staticmethod
    def search(db: Session, search_term: str, limit: int = 50) -> Sequence[ClientModel]:
        """
        Search clients by name, DNI, or phone number.

        Performs case-insensitive partial matching on multiple fields.

        Args:
            db: Database session.
            search_term: The search keyword to match against client data.
            limit: Maximum number of results to return (default: 50).

        Returns:
            List of ClientModel instances matching the search criteria.
        """
        search_pattern = f"%{search_term}%"
        stmt = select(ClientModel).where(
            or_(
                ClientModel.first_name.ilike(search_pattern),
                ClientModel.last_name.ilike(search_pattern),
                ClientModel.dni_number.ilike(search_pattern),
                ClientModel.phone.ilike(search_pattern),
            )
        ).limit(limit)
        return db.execute(stmt).scalars().all()

    @staticmethod
    def update(db: Session, client_id: UUID, **kwargs) -> Optional[ClientModel]:
        """
        Update a client's attributes by ID.

        Only non-None values are updated. Only existing attributes are modified.

        Args:
            db: Database session.
            client_id: The UUID of the client to update.
            **kwargs: Key-value pairs of attributes to update.

        Returns:
            Updated ClientModel if found, None otherwise.

        Example:
            client = ClientRepository.update(
                db, client_id,
                first_name="John",
                phone="+1234567890"
            )
        """
        stmt = select(ClientModel).where(ClientModel.id == client_id)
        client = db.execute(stmt).scalars().first()

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
        Soft delete a client by setting is_active to False.

        This preserves historical data for audit trails while marking
        the client as inactive.

        Args:
            db: Database session.
            client_id: The UUID of the client to delete.

        Returns:
            True if deletion was successful, False if client not found.
        """
        stmt = select(ClientModel).where(ClientModel.id == client_id)
        client = db.execute(stmt).scalars().first()

        if not client:
            return False

        client.is_active = False
        db.commit()
        return True

    @staticmethod
    def get_client_dashboard_data(db: Session, client_id: UUID) -> Optional[dict]:
        """
        Retrieve comprehensive client dashboard data in a single efficient query.

        Aggregates client info, biometric data, subscription history, and
        attendance statistics. Uses eager loading to minimize database hits.

        Args:
            db: Database session.
            client_id: The UUID of the client.

        Returns:
            Dictionary containing:
                - client: ClientModel instance
                - latest_subscription: Most recent SubscriptionModel
                - total_subscriptions: Total subscription count
                - last_attendance: Most recent AttendanceModel
                - attendance_count: Attendances since latest subscription start
            Returns None if client not found.

        Example:
            dashboard = ClientRepository.get_client_dashboard_data(db, client_id)
            if dashboard:
                print(f"Client: {dashboard['client'].first_name}")
                print(f"Attendances: {dashboard['attendance_count']}")
        """
        # Fetch client with biometrics eagerly loaded
        client_stmt = (
            select(ClientModel)
            .options(joinedload(ClientModel.biometrics))
            .where(ClientModel.id == client_id)
        )
        client = db.execute(client_stmt).scalars().unique().first()

        if not client:
            return None

        # Fetch latest subscription with plan details
        latest_sub_stmt = (
            select(SubscriptionModel)
            .options(joinedload(SubscriptionModel.plan))
            .where(SubscriptionModel.client_id == client_id)
            .order_by(SubscriptionModel.created_at.desc())
        )
        latest_subscription = db.execute(latest_sub_stmt).scalars().first()

        # Count total subscriptions
        total_subs_stmt = (
            select(func.count(SubscriptionModel.id)).where(
                SubscriptionModel.client_id == client_id
            )
        )
        total_subscriptions = db.execute(total_subs_stmt).scalar() or 0

        # Fetch last attendance record
        last_att_stmt = (
            select(AttendanceModel)
            .where(AttendanceModel.client_id == client_id)
            .order_by(AttendanceModel.check_in.desc())
        )
        last_attendance = db.execute(last_att_stmt).scalars().first()

        # Count attendances since latest subscription (if exists)
        attendance_count = 0
        if latest_subscription:
            att_count_stmt = (
                select(func.count(AttendanceModel.id)).where(
                    AttendanceModel.client_id == client_id,
                    AttendanceModel.check_in >= latest_subscription.start_date,
                )
            )
            attendance_count = db.execute(att_count_stmt).scalar() or 0

        return {
            "client": client,
            "latest_subscription": latest_subscription,
            "total_subscriptions": total_subscriptions,
            "last_attendance": last_attendance,
            "attendance_count": attendance_count,
        }