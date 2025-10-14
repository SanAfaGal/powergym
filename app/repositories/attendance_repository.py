from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import AttendanceModel, ClientModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class AttendanceRepository:
    @staticmethod
    def create(db: Session, client_id: UUID,
               meta_info: dict = None) -> AttendanceModel:
        """
        Create a new attendance record in the database.
        """
        db_attendance = AttendanceModel(
            client_id=client_id,
            meta_info=meta_info or {}
        )
        db.add(db_attendance)
        db.commit()
        db.refresh(db_attendance)
        return db_attendance

    @staticmethod
    def get_by_id(db: Session, attendance_id: UUID) -> Optional[AttendanceModel]:
        """
        Get attendance by ID.
        """
        return db.query(AttendanceModel).filter(AttendanceModel.id == attendance_id).first()

    @staticmethod
    def get_by_client_id(db: Session, client_id: UUID, limit: int = 100,
                        offset: int = 0) -> List[AttendanceModel]:
        """
        Get all attendance records for a specific client.
        """
        return db.query(AttendanceModel).filter(
            AttendanceModel.client_id == client_id
        ).order_by(AttendanceModel.check_in.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_all(db: Session, limit: int = 100, offset: int = 0) -> List[AttendanceModel]:
        """
        Get all attendance records.
        """
        return db.query(AttendanceModel).order_by(
            AttendanceModel.check_in.desc()
        ).offset(offset).limit(limit).all()

    @staticmethod
    def get_with_client_info(db: Session, limit: int = 100, offset: int = 0):
        """
        Get attendance records with client information.
        """
        return db.query(
            AttendanceModel,
            ClientModel.first_name,
            ClientModel.last_name,
            ClientModel.dni_number
        ).join(
            ClientModel, AttendanceModel.client_id == ClientModel.id
        ).order_by(
            AttendanceModel.check_in.desc()
        ).offset(offset).limit(limit).all()

    @staticmethod
    def get_by_date_range(db: Session, start_date: datetime, end_date: datetime,
                         limit: int = 1000, offset: int = 0) -> List[AttendanceModel]:
        """
        Get attendance records within a date range.
        """
        return db.query(AttendanceModel).filter(
            AttendanceModel.check_in >= start_date,
            AttendanceModel.check_in <= end_date
        ).order_by(AttendanceModel.check_in.desc()).offset(offset).limit(limit).all()

    @staticmethod
    async def create_async(db: AsyncSession, client_id: UUID,
                          meta_info: dict = None) -> AttendanceModel:
        """
        Create a new attendance record in the database (async).
        """
        db_attendance = AttendanceModel(
            client_id=client_id,
            meta_info=meta_info or {}
        )
        db.add(db_attendance)
        await db.commit()
        await db.refresh(db_attendance)
        return db_attendance

    @staticmethod
    async def get_by_id_async(db: AsyncSession, attendance_id: UUID) -> Optional[AttendanceModel]:
        """
        Get attendance by ID (async).
        """
        result = await db.execute(select(AttendanceModel).filter(AttendanceModel.id == attendance_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_client_id_async(db: AsyncSession, client_id: UUID,
                                    limit: int = 100, offset: int = 0) -> List[AttendanceModel]:
        """
        Get all attendance records for a specific client (async).
        """
        query = select(AttendanceModel).filter(
            AttendanceModel.client_id == client_id
        ).order_by(AttendanceModel.check_in.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_all_async(db: AsyncSession, limit: int = 100,
                           offset: int = 0) -> List[AttendanceModel]:
        """
        Get all attendance records (async).
        """
        query = select(AttendanceModel).order_by(
            AttendanceModel.check_in.desc()
        ).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_date_range_async(db: AsyncSession, start_date: datetime,
                                     end_date: datetime, limit: int = 1000,
                                     offset: int = 0) -> List[AttendanceModel]:
        """
        Get attendance records within a date range (async).
        """
        query = select(AttendanceModel).filter(
            AttendanceModel.check_in >= start_date,
            AttendanceModel.check_in <= end_date
        ).order_by(AttendanceModel.check_in.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
