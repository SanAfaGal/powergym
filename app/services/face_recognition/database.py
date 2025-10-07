"""
Database operations for face recognition biometric data.
Handles CRUD operations for face biometrics with encryption.
"""

from typing import List, Optional
from uuid import UUID

from app.core.database import get_supabase_client
from app.core.encryption import get_encryption_service
from app.models.biometric import BiometricType
from app.core.config import settings


class FaceDatabase:
    """Handles database operations for face biometric data."""

    @staticmethod
    def store_face_biometric(
        client_id: UUID,
        embedding: List[float],
        compressed_data: bytes,
        thumbnail: bytes
    ) -> dict:
        """
        Store face biometric data in database with encryption.

        Args:
            client_id: UUID of the client
            embedding: 512-dimensional face embedding
            compressed_data: Compressed face image bytes
            thumbnail: Thumbnail image bytes

        Returns:
            Dictionary with success status and biometric_id or error

        Raises:
            Exception: If database operation fails
        """
        try:
            supabase = get_supabase_client()

            existing_response = (
                supabase.table("client_biometrics")
                .select("id")
                .eq("client_id", str(client_id))
                .eq("type", BiometricType.FACE.value)
                .eq("is_active", True)
                .maybe_single()
                .execute()
            )

            if existing_response and existing_response.data:
                supabase.table("client_biometrics").update({
                    "is_active": False
                }).eq("id", existing_response.data["id"]).execute()

            encryption_service = get_encryption_service()

            encrypted_embedding = encryption_service.encrypt_embedding(embedding)
            encrypted_compressed_data = encryption_service.encrypt_image_data(
                compressed_data
            )
            encrypted_thumbnail = encryption_service.encrypt_image_data(thumbnail)

            biometric_data = {
                "client_id": str(client_id),
                "type": BiometricType.FACE.value,
                "compressed_data": encrypted_compressed_data,
                "thumbnail": encrypted_thumbnail,
                "embedding": encrypted_embedding,
                "is_active": True,
                "meta_info": {
                    "encoding_version": "face_recognition_v1_encrypted",
                    "model": settings.FACE_RECOGNITION_MODEL,
                    "encryption": "AES-256-GCM"
                }
            }

            response = supabase.table("client_biometrics").insert(biometric_data).execute()

            if response and response.data:
                return {
                    "success": True,
                    "biometric_id": response.data[0]["id"],
                    "client_id": str(client_id)
                }

            raise Exception("Failed to store biometric data")

        except Exception as e:
            return {
                "success": False,
                "error": f"Database operation failed: {str(e)}"
            }

    @staticmethod
    def get_all_active_face_biometrics() -> List[dict]:
        """
        Retrieve all active face biometric records from database.

        Returns:
            List of biometric records with encrypted data

        Raises:
            Exception: If database query fails
        """
        try:
            supabase = get_supabase_client()

            response = (
                supabase.table("client_biometrics")
                .select("id, client_id, embedding, meta_info")
                .eq("type", BiometricType.FACE.value)
                .eq("is_active", True)
                .execute()
            )

            if response and response.data:
                return response.data

            return []

        except Exception as e:
            raise Exception(f"Failed to retrieve biometric data: {str(e)}")

    @staticmethod
    def get_client_info(client_id: str) -> Optional[dict]:
        """
        Retrieve client information by ID.

        Args:
            client_id: UUID string of the client

        Returns:
            Client information dictionary or None if not found

        Raises:
            Exception: If database query fails
        """
        try:
            supabase = get_supabase_client()

            response = (
                supabase.table("clients")
                .select("*")
                .eq("id", client_id)
                .eq("is_active", True)
                .maybe_single()
                .execute()
            )

            if response and response.data:
                return response.data

            return None

        except Exception as e:
            raise Exception(f"Failed to retrieve client info: {str(e)}")

    @staticmethod
    def deactivate_face_biometric(client_id: UUID) -> dict:
        """
        Deactivate all face biometric records for a client.

        Args:
            client_id: UUID of the client

        Returns:
            Dictionary with success status

        Raises:
            Exception: If database operation fails
        """
        try:
            supabase = get_supabase_client()

            response = (
                supabase.table("client_biometrics")
                .update({"is_active": False})
                .eq("client_id", str(client_id))
                .eq("type", BiometricType.FACE.value)
                .execute()
            )

            if response:
                return {
                    "success": True,
                    "message": "Face biometric deactivated successfully"
                }

            return {
                "success": False,
                "error": "Failed to deactivate face biometric"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Database operation failed: {str(e)}"
            }
