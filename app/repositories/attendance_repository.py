# ============================================================================
# attendance/repository.py - SYNC VERSION
# ============================================================================

from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import AttendanceModel, ClientModel


class AttendanceRepository:
    """
    Repositorio para operaciones de base de datos con Attendances.

    Proporciona métodos para CRUD y consultas avanzadas de forma síncrona.
    """

    @staticmethod
    def create(
            db: Session,
            client_id: UUID,
            meta_info: Optional[dict] = None
    ) -> AttendanceModel:
        """
        Crear un nuevo registro de asistencia.

        Args:
            db: Sesión de base de datos
            client_id: ID del cliente
            meta_info: Información adicional

        Returns:
            Modelo de asistencia creado
        """
        attendance = AttendanceModel(
            client_id=client_id,
            meta_info=meta_info or {}
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance

    @staticmethod
    def get_by_id(
            db: Session,
            attendance_id: UUID
    ) -> Optional[AttendanceModel]:
        """Obtener asistencia por ID."""
        return db.query(AttendanceModel).filter(
            AttendanceModel.id == attendance_id
        ).first()

    @staticmethod
    def get_by_client_id(
            db: Session,
            client_id: UUID,
            limit: int = 50,
            offset: int = 0
    ) -> List[AttendanceModel]:
        """Obtener todas las asistencias de un cliente."""
        return db.query(AttendanceModel).filter(
            AttendanceModel.client_id == client_id
        ).order_by(
            AttendanceModel.check_in.desc()
        ).offset(offset).limit(limit).all()

    @staticmethod
    def get_all(
            db: Session,
            limit: int = 100,
            offset: int = 0
    ) -> List[AttendanceModel]:
        """Obtener todas las asistencias."""
        return db.query(AttendanceModel).order_by(
            AttendanceModel.check_in.desc()
        ).offset(offset).limit(limit).all()

    @staticmethod
    def get_with_client_info(
            db: Session,
            limit: int = 100,
            offset: int = 0,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[tuple]:
        """
        Obtener asistencias con información del cliente.

        Returns:
            Lista de tuplas: (AttendanceModel, first_name, last_name, dni_number)
        """
        query = db.query(
            AttendanceModel,
            ClientModel.first_name,
            ClientModel.last_name,
            ClientModel.dni_number
        ).join(
            ClientModel, AttendanceModel.client_id == ClientModel.id
        ).order_by(
            AttendanceModel.check_in.desc()
        )

        if start_date:
            query = query.filter(AttendanceModel.check_in >= start_date)
        if end_date:
            query = query.filter(AttendanceModel.check_in <= end_date)

        return query.offset(offset).limit(limit).all()

    @staticmethod
    def has_attendance_today(
            db: Session,
            client_id: UUID,
            check_date: Optional[date] = None
    ) -> bool:
        """
        Verificar si el cliente ya tiene una asistencia registrada en el día especificado.

        Args:
            db: Sesión de base de datos
            client_id: ID del cliente
            check_date: Fecha a verificar (por defecto hoy)

        Returns:
            True si ya existe una asistencia, False en caso contrario
        """
        if check_date is None:
            check_date = date.today()

        start_of_day = datetime.combine(check_date, datetime.min.time())
        end_of_day = datetime.combine(check_date, datetime.max.time())

        existing = db.query(AttendanceModel).filter(
            AttendanceModel.client_id == client_id,
            AttendanceModel.check_in >= start_of_day,
            AttendanceModel.check_in <= end_of_day
        ).first()

        return existing is not None

    @staticmethod
    def get_today_attendance(
            db: Session,
            client_id: UUID,
            check_date: Optional[date] = None
    ) -> Optional[AttendanceModel]:
        """
        Obtener la asistencia del cliente para el día especificado.

        Args:
            db: Sesión de base de datos
            client_id: ID del cliente
            check_date: Fecha a buscar (por defecto hoy)

        Returns:
            AttendanceModel si existe, None en caso contrario
        """
        if check_date is None:
            check_date = date.today()

        start_of_day = datetime.combine(check_date, datetime.min.time())
        end_of_day = datetime.combine(check_date, datetime.max.time())

        return db.query(AttendanceModel).filter(
            AttendanceModel.client_id == client_id,
            AttendanceModel.check_in >= start_of_day,
            AttendanceModel.check_in <= end_of_day
        ).first()