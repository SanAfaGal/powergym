from app.models.client import Client, ClientCreate, ClientUpdate
from app.core.database import get_supabase_client
from uuid import UUID
from typing import List

class ClientService:
    @staticmethod
    def create_client(client_data: ClientCreate) -> Client | None:
        supabase = get_supabase_client()

        client_dict = {
            "dni_type": client_data.dni_type.value,
            "dni_number": client_data.dni_number,
            "first_name": client_data.first_name,
            "middle_name": client_data.middle_name,
            "last_name": client_data.last_name,
            "second_last_name": client_data.second_last_name,
            "phone": client_data.phone,
            "alternative_phone": client_data.alternative_phone,
            "birth_date": client_data.birth_date.isoformat(),
            "gender": client_data.gender.value,
            "address": client_data.address,
            "is_active": True
        }

        response = supabase.table("clients").insert(client_dict).execute()

        if response and response.data:
            return Client(**response.data[0])
        return None

    @staticmethod
    def get_client_by_id(client_id: UUID) -> Client | None:
        supabase = get_supabase_client()

        response = supabase.table("clients").select("*").eq("id", str(client_id)).maybe_single().execute()

        if response and response.data:
            return Client(**response.data)
        return None

    @staticmethod
    def get_client_by_dni(dni_number: str) -> Client | None:
        supabase = get_supabase_client()

        response = supabase.table("clients").select("*").eq("dni_number", dni_number).maybe_single().execute()

        if response and response.data:
            return Client(**response.data)
        return None

    @staticmethod
    def update_client(client_id: UUID, client_update: ClientUpdate) -> Client | None:
        supabase = get_supabase_client()

        update_dict = {}
        if client_update.dni_type is not None:
            update_dict["dni_type"] = client_update.dni_type.value
        if client_update.dni_number is not None:
            update_dict["dni_number"] = client_update.dni_number
        if client_update.first_name is not None:
            update_dict["first_name"] = client_update.first_name
        if client_update.middle_name is not None:
            update_dict["middle_name"] = client_update.middle_name
        if client_update.last_name is not None:
            update_dict["last_name"] = client_update.last_name
        if client_update.second_last_name is not None:
            update_dict["second_last_name"] = client_update.second_last_name
        if client_update.phone is not None:
            update_dict["phone"] = client_update.phone
        if client_update.alternative_phone is not None:
            update_dict["alternative_phone"] = client_update.alternative_phone
        if client_update.birth_date is not None:
            update_dict["birth_date"] = client_update.birth_date.isoformat()
        if client_update.gender is not None:
            update_dict["gender"] = client_update.gender.value
        if client_update.address is not None:
            update_dict["address"] = client_update.address
        if client_update.is_active is not None:
            update_dict["is_active"] = client_update.is_active

        if not update_dict:
            return ClientService.get_client_by_id(client_id)

        response = supabase.table("clients").update(update_dict).eq("id", str(client_id)).execute()

        if response and response.data:
            return Client(**response.data[0])
        return None

    @staticmethod
    def delete_client(client_id: UUID) -> bool:
        supabase = get_supabase_client()

        response = supabase.table("clients").update({
            "is_active": False
        }).eq("id", str(client_id)).execute()

        return bool(response and response.data)

    @staticmethod
    def list_clients(
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Client]:
        supabase = get_supabase_client()

        query = supabase.table("clients").select("*")

        if is_active is not None:
            query = query.eq("is_active", is_active)

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        response = query.execute()

        if response and response.data:
            return [Client(**client) for client in response.data]
        return []

    @staticmethod
    def search_clients(search_term: str, limit: int = 50) -> List[Client]:
        supabase = get_supabase_client()

        response = supabase.table("clients").select("*").or_(
            f"first_name.ilike.%{search_term}%,"
            f"last_name.ilike.%{search_term}%,"
            f"dni_number.ilike.%{search_term}%,"
            f"phone.ilike.%{search_term}%"
        ).limit(limit).execute()

        if response and response.data:
            return [Client(**client) for client in response.data]
        return []
