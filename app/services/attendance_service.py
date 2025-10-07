from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID

from app.core.database import get_supabase_client
from app.models.attendance import AttendanceCreate, AttendanceResponse, AttendanceWithClientInfo


class AttendanceService:
    """Service for managing client attendance records."""

    @staticmethod
    async def create_attendance(
        client_id: UUID,
        biometric_type: Optional[str] = None,
        meta_info: Optional[dict] = None
    ) -> AttendanceResponse:
        """
        Create a new attendance record for a validated client.

        Args:
            client_id: UUID of the client
            biometric_type: Type of biometric used for validation ('face' or 'fingerprint')
            meta_info: Additional metadata (confidence score, device info, etc.)

        Returns:
            AttendanceResponse with the created record

        Raises:
            Exception: If database operation fails
        """
        supabase = get_supabase_client()

        attendance_data = {
            "client_id": str(client_id),
            "check_in": datetime.utcnow().isoformat(),
            "biometric_type": biometric_type,
            "meta_info": meta_info or {}
        }

        response = supabase.table("attendances").insert(attendance_data).execute()

        if not response.data:
            raise Exception("Failed to create attendance record")

        return AttendanceResponse(**response.data[0])

    @staticmethod
    async def get_attendance_by_id(attendance_id: UUID) -> Optional[AttendanceResponse]:
        """
        Get an attendance record by ID.

        Args:
            attendance_id: UUID of the attendance record

        Returns:
            AttendanceResponse if found, None otherwise
        """
        supabase = get_supabase_client()

        response = supabase.table("attendances").select("*").eq(
            "id", str(attendance_id)
        ).maybeSingle().execute()

        if response.data:
            return AttendanceResponse(**response.data)
        return None

    @staticmethod
    async def get_client_attendances(
        client_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[AttendanceResponse]:
        """
        Get attendance records for a specific client.

        Args:
            client_id: UUID of the client
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of AttendanceResponse objects
        """
        supabase = get_supabase_client()

        response = supabase.table("attendances").select("*").eq(
            "client_id", str(client_id)
        ).order("check_in", desc=True).range(offset, offset + limit - 1).execute()

        return [AttendanceResponse(**record) for record in response.data]

    @staticmethod
    async def get_all_attendances(
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AttendanceWithClientInfo]:
        """
        Get all attendance records with client information.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)

        Returns:
            List of AttendanceWithClientInfo objects
        """
        supabase = get_supabase_client()

        query = supabase.table("attendances").select(
            "*, clients(first_name, last_name, dni_number)"
        ).order("check_in", desc=True)

        if start_date:
            query = query.gte("check_in", start_date.isoformat())
        if end_date:
            query = query.lte("check_in", end_date.isoformat())

        response = query.range(offset, offset + limit - 1).execute()

        result = []
        for record in response.data:
            client_info = record.pop("clients", {})
            attendance = AttendanceWithClientInfo(
                **record,
                client_first_name=client_info.get("first_name", ""),
                client_last_name=client_info.get("last_name", ""),
                client_dni_number=client_info.get("dni_number", "")
            )
            result.append(attendance)

        return result

    @staticmethod
    async def get_today_attendances() -> List[AttendanceWithClientInfo]:
        """
        Get all attendance records for today.

        Returns:
            List of AttendanceWithClientInfo objects for today
        """
        today = datetime.utcnow().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())

        return await AttendanceService.get_all_attendances(
            start_date=start_of_day,
            end_date=end_of_day,
            limit=1000
        )

    @staticmethod
    async def count_client_attendances(
        client_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Count attendance records for a client within a date range.

        Args:
            client_id: UUID of the client
            start_date: Start date for counting (inclusive)
            end_date: End date for counting (inclusive)

        Returns:
            Number of attendance records
        """
        supabase = get_supabase_client()

        query = supabase.table("attendances").select(
            "id", count="exact"
        ).eq("client_id", str(client_id))

        if start_date:
            query = query.gte("check_in", start_date.isoformat())
        if end_date:
            query = query.lte("check_in", end_date.isoformat())

        response = query.execute()

        return response.count if response.count is not None else 0
