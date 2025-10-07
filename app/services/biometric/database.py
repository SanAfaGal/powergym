"""
Database operations for biometric data.
Handles CRUD operations and queries for biometric records.
"""

from typing import Optional, List
from uuid import UUID

from app.core.database import get_supabase_client
from app.models.biometric import BiometricType


class BiometricDatabase:
    """Handles database operations for biometric data."""

    @staticmethod
    def insert_biometric(
        client_id: UUID,
        biometric_type: BiometricType,
        encrypted_compressed_data: str,
        encrypted_thumbnail: Optional[str],
        encrypted_embedding: Optional[str],
        meta_info: dict
    ) -> Optional[dict]:
        """
        Insert a new biometric record into the database.

        Args:
            client_id: UUID of the client
            biometric_type: Type of biometric data
            encrypted_compressed_data: Encrypted compressed image
            encrypted_thumbnail: Encrypted thumbnail image
            encrypted_embedding: Encrypted embedding vector
            meta_info: Metadata dictionary

        Returns:
            Inserted record or None if failed
        """
        try:
            supabase = get_supabase_client()

            data = {
                "client_id": str(client_id),
                "type": biometric_type.value,
                "compressed_data": encrypted_compressed_data,
                "thumbnail": encrypted_thumbnail,
                "embedding": encrypted_embedding,
                "is_active": True,
                "meta_info": meta_info
            }

            response = supabase.table("client_biometrics").insert(data).execute()

            if response and response.data:
                return response.data[0]

            return None

        except Exception as e:
            print(f"Error inserting biometric: {str(e)}")
            return None

    @staticmethod
    def get_biometric_by_id(biometric_id: UUID) -> Optional[dict]:
        """
        Retrieve a biometric record by ID.

        Args:
            biometric_id: UUID of the biometric record

        Returns:
            Biometric record or None if not found
        """
        try:
            supabase = get_supabase_client()

            response = (
                supabase.table("client_biometrics")
                .select("*")
                .eq("id", str(biometric_id))
                .maybe_single()
                .execute()
            )

            if response and response.data:
                return response.data

            return None

        except Exception as e:
            print(f"Error retrieving biometric: {str(e)}")
            return None

    @staticmethod
    def get_biometrics_by_client(
        client_id: UUID,
        biometric_type: Optional[BiometricType] = None,
        active_only: bool = True
    ) -> List[dict]:
        """
        Retrieve all biometric records for a client.

        Args:
            client_id: UUID of the client
            biometric_type: Optional filter by biometric type
            active_only: Only return active records

        Returns:
            List of biometric records
        """
        try:
            supabase = get_supabase_client()

            query = supabase.table("client_biometrics").select("*").eq(
                "client_id", str(client_id)
            )

            if biometric_type:
                query = query.eq("type", biometric_type.value)

            if active_only:
                query = query.eq("is_active", True)

            response = query.execute()

            if response and response.data:
                return response.data

            return []

        except Exception as e:
            print(f"Error retrieving biometrics: {str(e)}")
            return []

    @staticmethod
    def get_all_active_biometrics(
        biometric_type: Optional[BiometricType] = None
    ) -> List[dict]:
        """
        Retrieve all active biometric records, optionally filtered by type.

        Args:
            biometric_type: Optional filter by biometric type

        Returns:
            List of biometric records
        """
        try:
            supabase = get_supabase_client()

            query = supabase.table("client_biometrics").select("*").eq(
                "is_active", True
            )

            if biometric_type:
                query = query.eq("type", biometric_type.value)

            response = query.execute()

            if response and response.data:
                return response.data

            return []

        except Exception as e:
            print(f"Error retrieving biometrics: {str(e)}")
            return []

    @staticmethod
    def update_biometric(biometric_id: UUID, update_data: dict) -> Optional[dict]:
        """
        Update a biometric record.

        Args:
            biometric_id: UUID of the biometric to update
            update_data: Dictionary of fields to update

        Returns:
            Updated record or None if failed
        """
        try:
            supabase = get_supabase_client()

            if not update_data:
                return BiometricDatabase.get_biometric_by_id(biometric_id)

            response = (
                supabase.table("client_biometrics")
                .update(update_data)
                .eq("id", str(biometric_id))
                .execute()
            )

            if response and response.data:
                return response.data[0]

            return None

        except Exception as e:
            print(f"Error updating biometric: {str(e)}")
            return None

    @staticmethod
    def deactivate_biometric(biometric_id: UUID) -> bool:
        """
        Soft delete a biometric record by setting is_active to False.

        Args:
            biometric_id: UUID of the biometric to deactivate

        Returns:
            True if successful, False otherwise
        """
        try:
            supabase = get_supabase_client()

            response = (
                supabase.table("client_biometrics")
                .update({"is_active": False})
                .eq("id", str(biometric_id))
                .execute()
            )

            return bool(response and response.data)

        except Exception as e:
            print(f"Error deactivating biometric: {str(e)}")
            return False

    @staticmethod
    def get_client_info(client_id: str) -> Optional[dict]:
        """
        Retrieve client information by ID.

        Args:
            client_id: UUID string of the client

        Returns:
            Client information or None if not found
        """
        try:
            supabase = get_supabase_client()

            response = (
                supabase.table("clients")
                .select("*")
                .eq("id", client_id)
                .maybe_single()
                .execute()
            )

            if response and response.data:
                return response.data

            return None

        except Exception as e:
            print(f"Error retrieving client info: {str(e)}")
            return None
