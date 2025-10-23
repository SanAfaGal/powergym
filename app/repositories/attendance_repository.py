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
    def count_by_client(
            db: Session,
            client_id: UUID,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> int:
        """Contar asistencias de un cliente en un período."""
        query = db.query(func.count(AttendanceModel.id)).filter(
            AttendanceModel.client_id == client_id
        )

        if start_date:
            query = query.filter(AttendanceModel.check_in >= start_date)
        if end_date:
            query = query.filter(AttendanceModel.check_in <= end_date)

        return query.scalar() or 0

    @staticmethod
    def get_today(
            db: Session,
            limit: int = 1000,
            offset: int = 0
    ) -> List[tuple]:
        """Obtener asistencias de hoy con info del cliente."""
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())

        return AttendanceRepository.get_with_client_info(
            db=db,
            limit=limit,
            offset=offset,
            start_date=start_of_day,
            end_date=end_of_day
        )