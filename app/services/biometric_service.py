from app.models.biometric import (
    Biometric,
    BiometricCreate,
    BiometricUpdate,
    BiometricType,
    BiometricSearchResult
)
from app.core.database import get_supabase_client
from uuid import UUID
from typing import List, Optional
import base64

class BiometricService:
    @staticmethod
    def create_biometric(biometric_data: BiometricCreate) -> Optional[Biometric]:
        supabase = get_supabase_client()

        biometric_dict = {
            "client_id": str(biometric_data.client_id),
            "type": biometric_data.type.value,
            "compressed_data": base64.b64encode(biometric_data.compressed_data).decode('utf-8'),
            "is_active": True,
            "meta_info": biometric_data.meta_info
        }

        if biometric_data.thumbnail:
            biometric_dict["thumbnail"] = base64.b64encode(biometric_data.thumbnail).decode('utf-8')

        if biometric_data.embedding:
            biometric_dict["embedding"] = biometric_data.embedding

        response = supabase.table("client_biometrics").insert(biometric_dict).execute()

        if response and response.data:
            return BiometricService._parse_biometric(response.data[0])
        return None

    @staticmethod
    def get_biometric_by_id(biometric_id: UUID) -> Optional[Biometric]:
        supabase = get_supabase_client()

        response = supabase.table("client_biometrics").select("*").eq("id", str(biometric_id)).maybe_single().execute()

        if response and response.data:
            return BiometricService._parse_biometric(response.data)
        return None

    @staticmethod
    def get_biometrics_by_client(
        client_id: UUID,
        biometric_type: Optional[BiometricType] = None,
        is_active: Optional[bool] = None
    ) -> List[Biometric]:
        supabase = get_supabase_client()

        query = supabase.table("client_biometrics").select("*").eq("client_id", str(client_id))

        if biometric_type:
            query = query.eq("type", biometric_type.value)

        if is_active is not None:
            query = query.eq("is_active", is_active)

        query = query.order("created_at", desc=True)

        response = query.execute()

        if response and response.data:
            return [BiometricService._parse_biometric(bio) for bio in response.data]
        return []

    @staticmethod
    def update_biometric(biometric_id: UUID, biometric_update: BiometricUpdate) -> Optional[Biometric]:
        supabase = get_supabase_client()

        update_dict = {}

        if biometric_update.compressed_data is not None:
            update_dict["compressed_data"] = base64.b64encode(biometric_update.compressed_data).decode('utf-8')

        if biometric_update.thumbnail is not None:
            update_dict["thumbnail"] = base64.b64encode(biometric_update.thumbnail).decode('utf-8')

        if biometric_update.embedding is not None:
            update_dict["embedding"] = biometric_update.embedding

        if biometric_update.is_active is not None:
            update_dict["is_active"] = biometric_update.is_active

        if biometric_update.meta_info is not None:
            update_dict["meta_info"] = biometric_update.meta_info

        if not update_dict:
            return BiometricService.get_biometric_by_id(biometric_id)

        response = supabase.table("client_biometrics").update(update_dict).eq("id", str(biometric_id)).execute()

        if response and response.data:
            return BiometricService._parse_biometric(response.data[0])
        return None

    @staticmethod
    def delete_biometric(biometric_id: UUID) -> bool:
        supabase = get_supabase_client()

        response = supabase.table("client_biometrics").delete().eq("id", str(biometric_id)).execute()

        return bool(response and response.data)

    @staticmethod
    def deactivate_biometric(biometric_id: UUID) -> Optional[Biometric]:
        supabase = get_supabase_client()

        response = supabase.table("client_biometrics").update({
            "is_active": False
        }).eq("id", str(biometric_id)).execute()

        if response and response.data:
            return BiometricService._parse_biometric(response.data[0])
        return None

    @staticmethod
    def search_by_embedding(
        embedding: List[float],
        biometric_type: Optional[BiometricType] = None,
        limit: int = 10,
        similarity_threshold: float = 0.8
    ) -> List[BiometricSearchResult]:
        supabase = get_supabase_client()

        rpc_params = {
            "query_embedding": embedding,
            "match_threshold": similarity_threshold,
            "match_count": limit
        }

        if biometric_type:
            rpc_params["filter_type"] = biometric_type.value

        try:
            response = supabase.rpc("match_biometrics", rpc_params).execute()

            if response and response.data:
                results = []
                for item in response.data:
                    biometric = BiometricService._parse_biometric(item)
                    result = BiometricSearchResult(
                        biometric=biometric,
                        similarity=item.get("similarity", 0.0),
                        customer_info=item.get("customer_info")
                    )
                    results.append(result)
                return results
        except Exception:
            pass

        return []

    @staticmethod
    def list_biometrics(
        biometric_type: Optional[BiometricType] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Biometric]:
        supabase = get_supabase_client()

        query = supabase.table("client_biometrics").select("*")

        if biometric_type:
            query = query.eq("type", biometric_type.value)

        if is_active is not None:
            query = query.eq("is_active", is_active)

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        response = query.execute()

        if response and response.data:
            return [BiometricService._parse_biometric(bio) for bio in response.data]
        return []

    @staticmethod
    def _parse_biometric(data: dict) -> Biometric:
        parsed_data = data.copy()

        if "compressed_data" in parsed_data and parsed_data["compressed_data"]:
            parsed_data["compressed_data"] = base64.b64decode(parsed_data["compressed_data"])

        if "thumbnail" in parsed_data and parsed_data["thumbnail"]:
            parsed_data["thumbnail"] = base64.b64decode(parsed_data["thumbnail"])

        return Biometric(**parsed_data)
