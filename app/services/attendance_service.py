from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.attendance_repository import AttendanceRepository
from app.db.models import AttendanceModel, ClientModel
from app.models.attendance import AttendanceResponse, AttendanceWithClientInfo


class AttendanceService:

    @staticmethod
    async def create_attendance(
        db: AsyncSession,
        client_id: UUID,
        biometric_type: Optional[str] = None,
        meta_info: Optional[dict] = None
    ) -> AttendanceResponse:
        attendance_model = await AttendanceRepository.create_async(
            db=db,
            client_id=client_id,
            biometric_type=biometric_type,
            meta_info=meta_info or {}
        )

        return AttendanceResponse(
            id=attendance_model.id,
            client_id=attendance_model.client_id,
            check_in=attendance_model.check_in,
            biometric_type=attendance_model.biometric_type,
            meta_info=attendance_model.meta_info
        )

    @staticmethod
    async def get_attendance_by_id(db: AsyncSession, attendance_id: UUID) -> Optional[AttendanceResponse]:
        attendance_model = await AttendanceRepository.get_by_id_async(db, attendance_id)

        if attendance_model:
            return AttendanceResponse(
                id=attendance_model.id,
                client_id=attendance_model.client_id,
                check_in=attendance_model.check_in,
                biometric_type=attendance_model.biometric_type,
                meta_info=attendance_model.meta_info
            )
        return None

    @staticmethod
    async def get_client_attendances(
        db: AsyncSession,
        client_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[AttendanceResponse]:
        attendance_models = await AttendanceRepository.get_by_client_id_async(
            db, client_id, limit, offset
        )

        return [
            AttendanceResponse(
                id=att.id,
                client_id=att.client_id,
                check_in=att.check_in,
                biometric_type=att.biometric_type,
                meta_info=att.meta_info
            )
            for att in attendance_models
        ]

    @staticmethod
    async def get_all_attendances(
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AttendanceWithClientInfo]:
        if start_date and end_date:
            query = select(
                AttendanceModel,
                ClientModel.first_name,
                ClientModel.last_name,
                ClientModel.dni_number
            ).join(
                ClientModel, AttendanceModel.client_id == ClientModel.id
            ).where(
                AttendanceModel.check_in >= start_date,
                AttendanceModel.check_in <= end_date
            ).order_by(AttendanceModel.check_in.desc()).offset(offset).limit(limit)
        else:
            query = select(
                AttendanceModel,
                ClientModel.first_name,
                ClientModel.last_name,
                ClientModel.dni_number
            ).join(
                ClientModel, AttendanceModel.client_id == ClientModel.id
            ).order_by(AttendanceModel.check_in.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        return [
            AttendanceWithClientInfo(
                id=att.id,
                client_id=att.client_id,
                check_in=att.check_in,
                biometric_type=att.biometric_type,
                meta_info=att.meta_info,
                client_first_name=first_name,
                client_last_name=last_name,
                client_dni_number=dni_number
            )
            for att, first_name, last_name, dni_number in rows
        ]

    @staticmethod
    async def get_today_attendances(db: AsyncSession) -> List[AttendanceWithClientInfo]:
        today = datetime.utcnow().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())

        return await AttendanceService.get_all_attendances(
            db=db,
            start_date=start_of_day,
            end_date=end_of_day,
            limit=1000
        )

    @staticmethod
    async def count_client_attendances(
        db: AsyncSession,
        client_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        from sqlalchemy import func

        query = select(func.count(AttendanceModel.id)).where(
            AttendanceModel.client_id == client_id
        )

        if start_date:
            query = query.where(AttendanceModel.check_in >= start_date)
        if end_date:
            query = query.where(AttendanceModel.check_in <= end_date)

        result = await db.execute(query)
        return result.scalar() or 0
